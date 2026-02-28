import { chromium } from 'playwright';
import fs from 'fs';

const BASE_URL = 'http://localhost:3000';

const VIEWPORTS = [
  { name: 'Mobile', width: 375, height: 812 },
  { name: 'Tablet', width: 768, height: 1024 },
  { name: 'Desktop', width: 1440, height: 900 },
];

const PAGES = [
  // Public
  { path: '/', name: 'Anasayfa', group: 'Public' },
  { path: '/login', name: 'Login', group: 'Public' },
  { path: '/register', name: 'Register', group: 'Public' },
  // Dashboard
  { path: '/dashboard', name: 'Dashboard Ana', group: 'Dashboard' },
  { path: '/valuations', name: 'Valuations', group: 'Dashboard' },
  { path: '/properties', name: 'Properties', group: 'Dashboard' },
  { path: '/customers', name: 'Customers', group: 'Dashboard' },
  { path: '/areas', name: 'Areas', group: 'Dashboard' },
  { path: '/maps', name: 'Maps', group: 'Dashboard' },
  { path: '/listings', name: 'Listings', group: 'Dashboard' },
  { path: '/calculator', name: 'Calculator', group: 'Dashboard' },
  { path: '/network', name: 'Network', group: 'Dashboard' },
  { path: '/messages', name: 'Messages', group: 'Dashboard' },
  { path: '/settings', name: 'Settings', group: 'Dashboard' },
  // Telegram Mini App
  { path: '/tg', name: 'TG Ana', group: 'Telegram' },
  { path: '/tg/valuation', name: 'TG Valuation', group: 'Telegram' },
  { path: '/tg/crm', name: 'TG CRM', group: 'Telegram' },
];

async function runTests() {
  const results = [];
  const allLinks = new Set();
  const allConsoleErrors = [];

  const browser = await chromium.launch({ headless: true });

  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: viewport.name === 'Mobile' ? 2 : 1,
    });

    for (const pageInfo of PAGES) {
      const page = await context.newPage();
      const consoleErrors = [];
      const consoleWarnings = [];

      // Listen for console errors
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
        if (msg.type() === 'warning') {
          consoleWarnings.push(msg.text());
        }
      });

      // Listen for page errors
      page.on('pageerror', (error) => {
        consoleErrors.push(`PageError: ${error.message}`);
      });

      const url = `${BASE_URL}${pageInfo.path}`;
      let httpStatus = 0;
      let loadTime = 0;
      let overflowIssues = [];
      let brokenImages = [];
      let links = [];
      let redirectedTo = null;
      let pageTitle = '';

      try {
        const startTime = Date.now();
        const response = await page.goto(url, {
          waitUntil: 'networkidle',
          timeout: 15000
        });
        loadTime = Date.now() - startTime;
        httpStatus = response?.status() || 0;

        // Check if redirected
        const finalUrl = page.url();
        if (finalUrl !== url && finalUrl !== url + '/') {
          redirectedTo = finalUrl.replace(BASE_URL, '');
        }

        pageTitle = await page.title();

        // Wait a moment for dynamic content
        await page.waitForTimeout(1000);

        // Check for horizontal overflow
        overflowIssues = await page.evaluate(() => {
          const issues = [];
          const docWidth = document.documentElement.scrollWidth;
          const viewWidth = window.innerWidth;

          if (docWidth > viewWidth + 5) {
            issues.push(`Document overflow: ${docWidth}px > viewport ${viewWidth}px (+${docWidth - viewWidth}px)`);
          }

          // Check individual elements
          const allElements = document.querySelectorAll('*');
          for (const el of allElements) {
            const rect = el.getBoundingClientRect();
            if (rect.right > viewWidth + 5 && el.offsetWidth > 0) {
              const tag = el.tagName.toLowerCase();
              const cls = el.className?.toString().slice(0, 60) || '';
              const id = el.id ? `#${el.id}` : '';
              issues.push(`Element overflow: <${tag}${id}> .${cls} — right: ${Math.round(rect.right)}px`);
              if (issues.length > 5) break; // Limit
            }
          }

          // Check text overflow/truncation issues
          const textEls = document.querySelectorAll('h1,h2,h3,h4,p,span,a,td,th,li,button,label');
          for (const el of textEls) {
            if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) {
              const style = getComputedStyle(el);
              const hasOverflowHandling = style.overflow === 'hidden' ||
                style.textOverflow === 'ellipsis' ||
                style.whiteSpace === 'nowrap';
              if (!hasOverflowHandling) {
                const text = el.textContent?.slice(0, 30) || '';
                issues.push(`Text overflow: "${text}..." (scrollW: ${el.scrollWidth}, clientW: ${el.clientWidth})`);
                if (issues.length > 8) break;
              }
            }
          }

          return issues;
        });

        // Check broken images
        brokenImages = await page.evaluate(() => {
          const imgs = document.querySelectorAll('img');
          const broken = [];
          for (const img of imgs) {
            if (!img.complete || img.naturalWidth === 0) {
              broken.push(img.src || img.getAttribute('src') || 'unknown');
            }
          }
          return broken;
        });

        // Collect all links
        links = await page.evaluate(() => {
          const anchors = document.querySelectorAll('a[href]');
          return Array.from(anchors).map(a => ({
            href: a.getAttribute('href'),
            text: a.textContent?.trim().slice(0, 50) || '',
          }));
        });

        for (const link of links) {
          allLinks.add(JSON.stringify(link));
        }

      } catch (error) {
        consoleErrors.push(`Navigation error: ${error.message}`);
      }

      // Filter out common non-critical warnings
      const criticalErrors = consoleErrors.filter(e =>
        !e.includes('favicon') &&
        !e.includes('Hydration') &&
        !e.includes('downloadable font')
      );

      const hydrationErrors = consoleErrors.filter(e => e.includes('Hydration'));

      results.push({
        group: pageInfo.group,
        page: pageInfo.name,
        path: pageInfo.path,
        viewport: viewport.name,
        resolution: `${viewport.width}x${viewport.height}`,
        httpStatus,
        redirectedTo,
        pageTitle,
        loadTime,
        consoleErrors: criticalErrors,
        hydrationErrors,
        consoleWarnings,
        overflowIssues,
        brokenImages,
        linkCount: links.length,
      });

      if (criticalErrors.length > 0) {
        allConsoleErrors.push({
          page: `${pageInfo.name} (${viewport.name})`,
          errors: criticalErrors,
        });
      }

      await page.close();
    }

    await context.close();
  }

  await browser.close();

  // Parse all links
  const uniqueLinks = [...allLinks].map(l => JSON.parse(l));

  // Output JSON results
  const output = {
    timestamp: new Date().toISOString(),
    results,
    allLinks: uniqueLinks,
    consoleErrorSummary: allConsoleErrors,
    summary: {
      totalTests: results.length,
      passed: results.filter(r => r.httpStatus === 200 && r.consoleErrors.length === 0 && r.overflowIssues.length === 0 && r.brokenImages.length === 0).length,
      httpErrors: results.filter(r => r.httpStatus !== 200 && !r.redirectedTo).length,
      redirects: results.filter(r => r.redirectedTo).length,
      withConsoleErrors: results.filter(r => r.consoleErrors.length > 0).length,
      withOverflow: results.filter(r => r.overflowIssues.length > 0).length,
      withBrokenImages: results.filter(r => r.brokenImages.length > 0).length,
      withHydrationErrors: results.filter(r => r.hydrationErrors.length > 0).length,
      totalLinks: uniqueLinks.length,
    },
  };

  fs.writeFileSync('/Users/ferit/Projeler/Emlak/apps/web/test-results.json', JSON.stringify(output, null, 2));
  console.log(JSON.stringify(output.summary, null, 2));
  console.log('\n--- DETAILS ---\n');

  for (const r of results) {
    const status = (r.httpStatus === 200 || r.redirectedTo) ? '✅' : '❌';
    const overflow = r.overflowIssues.length > 0 ? '⚠️ OVERFLOW' : '';
    const errors = r.consoleErrors.length > 0 ? `🔴 ${r.consoleErrors.length} errors` : '';
    const redirect = r.redirectedTo ? `→ ${r.redirectedTo}` : '';
    console.log(`${status} ${r.viewport.padEnd(7)} ${r.page.padEnd(16)} HTTP:${r.httpStatus} ${r.loadTime}ms ${overflow} ${errors} ${redirect}`);

    if (r.overflowIssues.length > 0) {
      for (const issue of r.overflowIssues) {
        console.log(`   ⚠️  ${issue}`);
      }
    }
    if (r.consoleErrors.length > 0) {
      for (const err of r.consoleErrors) {
        console.log(`   🔴 ${err.slice(0, 150)}`);
      }
    }
    if (r.brokenImages.length > 0) {
      for (const img of r.brokenImages) {
        console.log(`   🖼️  Broken: ${img}`);
      }
    }
  }
}

runTests().catch(console.error);

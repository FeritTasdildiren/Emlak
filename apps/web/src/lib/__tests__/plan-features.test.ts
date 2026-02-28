import { describe, it, expect } from "vitest";
import { PLAN_CONFIGS, checkFeatureAccess, type FeatureKey } from "../plan-features";
import type { PlanType } from "@/types/plan";

describe("PLAN_CONFIGS", () => {
  // ─── Yapısal Kontroller ────────────────────────────────────

  it("3 plan tipi tanımlı olmalı: starter, pro, elite", () => {
    const planTypes = Object.keys(PLAN_CONFIGS);
    expect(planTypes).toHaveLength(3);
    expect(planTypes).toContain("starter");
    expect(planTypes).toContain("pro");
    expect(planTypes).toContain("elite");
  });

  it("her planın tüm feature key'leri olmalı", () => {
    const expectedKeys: FeatureKey[] = [
      "valuationMonthlyLimit",
      "crmContactLimit",
      "showcaseLimit",
      "hasAiAssistant",
      "hasVirtualStaging",
      "hasPortalExport",
      "hasSharingNetwork",
    ];

    for (const plan of Object.values(PLAN_CONFIGS)) {
      for (const key of expectedKeys) {
        expect(plan).toHaveProperty(key);
      }
    }
  });

  // ─── Starter Plan ─────────────────────────────────────────

  it("starter plan — limitler düşük ve premium özellikler kapalı", () => {
    const starter = PLAN_CONFIGS.starter;

    expect(starter.valuationMonthlyLimit).toBe(50);
    expect(starter.crmContactLimit).toBe(50);
    expect(starter.showcaseLimit).toBe(1);
    expect(starter.hasAiAssistant).toBe(false);
    expect(starter.hasVirtualStaging).toBe(false);
    expect(starter.hasPortalExport).toBe(false);
    expect(starter.hasSharingNetwork).toBe(false);
  });

  // ─── Pro Plan ──────────────────────────────────────────────

  it("pro plan — limitler orta, bazı premium özellikler açık", () => {
    const pro = PLAN_CONFIGS.pro;

    expect(pro.valuationMonthlyLimit).toBe(500);
    expect(pro.crmContactLimit).toBe(500);
    expect(pro.showcaseLimit).toBe(5);
    expect(pro.hasAiAssistant).toBe(true);
    expect(pro.hasVirtualStaging).toBe(false); // Pro'da yok
    expect(pro.hasPortalExport).toBe(true);
    expect(pro.hasSharingNetwork).toBe(true);
  });

  // ─── Elite Plan ────────────────────────────────────────────

  it("elite plan — limitler sınırsız, tüm özellikler açık", () => {
    const elite = PLAN_CONFIGS.elite;

    expect(elite.valuationMonthlyLimit).toBe(Infinity);
    expect(elite.crmContactLimit).toBe(Infinity);
    expect(elite.showcaseLimit).toBe(Infinity);
    expect(elite.hasAiAssistant).toBe(true);
    expect(elite.hasVirtualStaging).toBe(true);
    expect(elite.hasPortalExport).toBe(true);
    expect(elite.hasSharingNetwork).toBe(true);
  });

  // ─── Hiyerarşi Kontrolleri ─────────────────────────────────

  it("üst planlar alt planlardan her zaman daha fazla veya eşit limit sağlar", () => {
    const plans: PlanType[] = ["starter", "pro", "elite"];
    const numericKeys: FeatureKey[] = [
      "valuationMonthlyLimit",
      "crmContactLimit",
      "showcaseLimit",
    ];

    for (let i = 0; i < plans.length - 1; i++) {
      const lower = PLAN_CONFIGS[plans[i]];
      const higher = PLAN_CONFIGS[plans[i + 1]];

      for (const key of numericKeys) {
        expect(higher[key]).toBeGreaterThanOrEqual(lower[key] as number);
      }
    }
  });

  it("üst planlar alt planlardaki boolean özellikleri de içerir", () => {
    const booleanKeys: FeatureKey[] = [
      "hasAiAssistant",
      "hasVirtualStaging",
      "hasPortalExport",
      "hasSharingNetwork",
    ];

    // Pro, starter'ın true olan feature'larını da true yapmalı
    for (const key of booleanKeys) {
      if (PLAN_CONFIGS.starter[key] === true) {
        expect(PLAN_CONFIGS.pro[key]).toBe(true);
      }
      if (PLAN_CONFIGS.pro[key] === true) {
        expect(PLAN_CONFIGS.elite[key]).toBe(true);
      }
    }
  });
});

describe("checkFeatureAccess", () => {
  it("starter planında AI assistant erişimi false döner", () => {
    expect(checkFeatureAccess("starter", "hasAiAssistant")).toBe(false);
  });

  it("pro planında AI assistant erişimi true döner", () => {
    expect(checkFeatureAccess("pro", "hasAiAssistant")).toBe(true);
  });

  it("elite planında virtual staging erişimi true döner", () => {
    expect(checkFeatureAccess("elite", "hasVirtualStaging")).toBe(true);
  });

  it("starter planında valuation limiti 50 döner", () => {
    expect(checkFeatureAccess("starter", "valuationMonthlyLimit")).toBe(50);
  });

  it("elite planında valuation limiti Infinity döner", () => {
    expect(checkFeatureAccess("elite", "valuationMonthlyLimit")).toBe(Infinity);
  });
});

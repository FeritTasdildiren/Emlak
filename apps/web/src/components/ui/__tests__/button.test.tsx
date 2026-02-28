import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "../button";

describe("Button", () => {
  // ─── Render ────────────────────────────────────────────────

  it("children ile doğru şekilde render edilir", () => {
    render(<Button>Kaydet</Button>);
    expect(screen.getByRole("button", { name: "Kaydet" })).toBeInTheDocument();
  });

  it("button HTML elementi olarak render edilir", () => {
    render(<Button>Test</Button>);
    const button = screen.getByRole("button");
    expect(button.tagName).toBe("BUTTON");
  });

  // ─── Variants ──────────────────────────────────────────────

  it("default variant doğru sınıfları içerir", () => {
    render(<Button variant="default">Varsayılan</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("bg-blue-600");
  });

  it("destructive variant kırmızı arka plana sahip olur", () => {
    render(<Button variant="destructive">Sil</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("bg-red-600");
  });

  it("outline variant border içerir", () => {
    render(<Button variant="outline">İptal</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("border");
  });

  // ─── Sizes ─────────────────────────────────────────────────

  it("sm boyutu doğru sınıfları uygular", () => {
    render(<Button size="sm">Küçük</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("h-9");
  });

  it("lg boyutu doğru sınıfları uygular", () => {
    render(<Button size="lg">Büyük</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("h-11");
  });

  // ─── Disabled ──────────────────────────────────────────────

  it("disabled olduğunda tıklanamaz", async () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        Pasif
      </Button>
    );

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();

    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  // ─── Loading ───────────────────────────────────────────────

  it("loading durumunda buton disabled olur", () => {
    render(<Button loading>Yükleniyor</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("loading durumunda spinner SVG gösterilir", () => {
    render(<Button loading>Yükleniyor</Button>);
    const button = screen.getByRole("button");
    const svg = button.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg!.classList.contains("animate-spin")).toBe(true);
  });

  // ─── Click ─────────────────────────────────────────────────

  it("tıklandığında onClick handler çağrılır", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Tıkla</Button>);

    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  // ─── FullWidth ─────────────────────────────────────────────

  it("fullWidth prop ile tam genişlik sınıfı eklenir", () => {
    render(<Button fullWidth>Tam Genişlik</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("w-full");
  });

  // ─── Custom className ──────────────────────────────────────

  it("ek className prop ile özel sınıf eklenebilir", () => {
    render(<Button className="my-custom-class">Özel</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("my-custom-class");
  });
});

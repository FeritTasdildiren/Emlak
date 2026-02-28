"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Globe,
  Eye,
  Pencil,
  Link2,
  Plus,
  LayoutGrid,
  Clock,
  Store,
  Users,
  ExternalLink,
  Building2,
  User,
  Lock,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useShowcases } from "@/hooks/use-showcases";
import { useSharedShowcases } from "@/hooks/use-shared-showcases";
import { formatDate } from "@/lib/utils";
import type { Showcase } from "@/types/showcase";
import type { SharedShowcase } from "@/hooks/use-shared-showcases";
import { FeatureGate } from "@/components/feature-gate";
import { usePlan } from "@/hooks/use-plan";

// ─── Showcase Card ──────────────────────────────────────────────
function ShowcaseCard({ showcase }: { showcase: Showcase }) {
  const [copied, setCopied] = useState(false);

  const showcaseUrl = `${typeof window !== "undefined" ? window.location.origin : ""}/vitrin/${showcase.slug}`;

  function handleCopyLink() {
    navigator.clipboard.writeText(showcaseUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <Card className="group transition-all hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {showcase.title}
            </h3>
            <p className="mt-1 text-sm text-gray-500 font-mono">
              /vitrin/{showcase.slug}
            </p>
          </div>
          <Badge
            variant={showcase.is_active ? "success" : "secondary"}
            className="shrink-0"
          >
            {showcase.is_active ? "Yayında" : "Taslak"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        {showcase.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
            {showcase.description}
          </p>
        )}

        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col items-center rounded-lg bg-gray-50 p-3">
            <LayoutGrid className="h-4 w-4 text-gray-400 mb-1" />
            <span className="text-lg font-semibold text-gray-900">
              {showcase.selected_properties.length}
            </span>
            <span className="text-xs text-gray-500">İlan</span>
          </div>
          <div className="flex flex-col items-center rounded-lg bg-gray-50 p-3">
            <Eye className="h-4 w-4 text-gray-400 mb-1" />
            <span className="text-lg font-semibold text-gray-900">
              {showcase.views_count}
            </span>
            <span className="text-xs text-gray-500">Görüntüleme</span>
          </div>
          <div className="flex flex-col items-center rounded-lg bg-gray-50 p-3">
            <Clock className="h-4 w-4 text-gray-400 mb-1" />
            <span className="text-sm font-medium text-gray-900">
              {formatDate(showcase.created_at)}
            </span>
            <span className="text-xs text-gray-500">Oluşturulma</span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="gap-2 flex-wrap">
        <Link href={`/network/${showcase.id}/edit`}>
          <Button variant="outline" size="sm" className="gap-1.5">
            <Pencil className="h-3.5 w-3.5" />
            Düzenle
          </Button>
        </Link>
        <Link href={`/vitrin/${showcase.slug}`} target="_blank">
          <Button variant="outline" size="sm" className="gap-1.5">
            <Eye className="h-3.5 w-3.5" />
            Görüntüle
          </Button>
        </Link>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={handleCopyLink}
        >
          <Link2 className="h-3.5 w-3.5" />
          {copied ? "Kopyalandı!" : "Linki Kopyala"}
        </Button>
      </CardFooter>
    </Card>
  );
}

// ─── Empty State ────────────────────────────────────────────────
function ShowcaseEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50/50 px-6 py-16 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-orange-100">
        <Store className="h-7 w-7 text-orange-600" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-gray-900">
        Henüz vitrin oluşturmadınız
      </h3>
      <p className="mt-2 max-w-sm text-sm text-gray-500">
        Müşterilerinize özel bir vitrin sayfası oluşturun ve seçtiğiniz ilanları
        tek bir bağlantıyla paylaşın.
      </p>
      <Link href="/network/create">
        <Button className="mt-6 gap-2 bg-orange-600 hover:bg-orange-700 text-white">
          <Plus className="h-4 w-4" />
          Yeni Vitrin Oluştur
        </Button>
      </Link>
    </div>
  );
}

// ─── Loading Skeleton ───────────────────────────────────────────
function ShowcaseLoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-10 w-44" />
      </div>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <Skeleton className="h-5 w-64" />
              <Skeleton className="h-4 w-40" />
            </div>
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <Skeleton className="h-4 w-full mb-4" />
          <div className="grid grid-cols-3 gap-3">
            <Skeleton className="h-20 rounded-lg" />
            <Skeleton className="h-20 rounded-lg" />
            <Skeleton className="h-20 rounded-lg" />
          </div>
        </CardContent>
        <CardFooter className="gap-2">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-28" />
          <Skeleton className="h-9 w-32" />
        </CardFooter>
      </Card>
    </div>
  );
}

// ─── Shared Showcase Card (Tab 2) ───────────────────────────────
function SharedShowcaseCard({ showcase }: { showcase: SharedShowcase }) {
  return (
    <Card className="group transition-all hover:shadow-md">
      <CardHeader className="pb-3">
        <h3 className="text-lg font-semibold text-gray-900 truncate">
          {showcase.title}
        </h3>
        {showcase.description && (
          <p className="text-sm text-gray-500 line-clamp-2 mt-1">
            {showcase.description}
          </p>
        )}
      </CardHeader>

      <CardContent className="pb-3 space-y-3">
        {/* Agent & Office Info */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <User className="h-4 w-4 text-gray-400 shrink-0" />
            <span className="font-medium truncate">{showcase.agent_name}</span>
          </div>
          {showcase.office_name && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Building2 className="h-4 w-4 text-gray-400 shrink-0" />
              <span className="truncate">{showcase.office_name}</span>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="flex flex-col items-center rounded-lg bg-gray-50 p-2.5">
            <LayoutGrid className="h-3.5 w-3.5 text-gray-400 mb-0.5" />
            <span className="text-base font-semibold text-gray-900">
              {showcase.property_count}
            </span>
            <span className="text-xs text-gray-500">İlan</span>
          </div>
          <div className="flex flex-col items-center rounded-lg bg-gray-50 p-2.5">
            <Eye className="h-3.5 w-3.5 text-gray-400 mb-0.5" />
            <span className="text-base font-semibold text-gray-900">
              {showcase.views_count}
            </span>
            <span className="text-xs text-gray-500">Görüntüleme</span>
          </div>
          <div className="flex flex-col items-center rounded-lg bg-gray-50 p-2.5">
            <Clock className="h-3.5 w-3.5 text-gray-400 mb-0.5" />
            <span className="text-xs font-medium text-gray-900">
              {formatDate(showcase.created_at)}
            </span>
            <span className="text-xs text-gray-500">Tarih</span>
          </div>
        </div>
      </CardContent>

      <CardFooter>
        <Link
          href={`/vitrin/${showcase.slug}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full"
        >
          <Button
            variant="outline"
            size="sm"
            className="w-full gap-1.5"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Görüntüle
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}

// ─── Sharing Network Empty State ────────────────────────────────
function SharingNetworkEmpty() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50/50 px-6 py-16 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-100">
        <Users className="h-7 w-7 text-blue-600" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-gray-900">
        Henüz paylaşıma açılmış vitrin yok
      </h3>
      <p className="mt-2 max-w-sm text-sm text-gray-500">
        Diğer ofisler vitrinlerini paylaşıma açtığında burada listelenecektir.
      </p>
    </div>
  );
}

// ─── Sharing Network Loading ────────────────────────────────────
function SharingNetworkSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-7 w-40" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-3">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full mt-1" />
            </CardHeader>
            <CardContent className="pb-3 space-y-3">
              <div className="space-y-1.5">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-40" />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <Skeleton className="h-16 rounded-lg" />
                <Skeleton className="h-16 rounded-lg" />
                <Skeleton className="h-16 rounded-lg" />
              </div>
            </CardContent>
            <CardFooter>
              <Skeleton className="h-9 w-full" />
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ─── Sharing Network (Tab 2) ────────────────────────────────────
function SharingNetwork() {
  const { showcases, isLoading } = useSharedShowcases();

  if (isLoading) {
    return <SharingNetworkSkeleton />;
  }

  if (showcases.length === 0) {
    return <SharingNetworkEmpty />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Paylaşım Ağı</h2>
        <Badge variant="secondary">
          {showcases.length} vitrin
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {showcases.map((showcase) => (
          <SharedShowcaseCard key={showcase.id} showcase={showcase} />
        ))}
      </div>
    </div>
  );
}

// ─── Vitrin Yönetimi (Tab 1) ────────────────────────────────────
function ShowcaseManagement() {
  const { showcases, isLoading } = useShowcases();

  if (isLoading) {
    return <ShowcaseLoadingSkeleton />;
  }

  if (showcases.length === 0) {
    return <ShowcaseEmptyState />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Vitrinim</h2>
        <Link href="/network/create">
          <Button className="gap-2 bg-orange-600 hover:bg-orange-700 text-white">
            <Plus className="h-4 w-4" />
            Yeni Vitrin Oluştur
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {showcases.map((showcase) => (
          <ShowcaseCard key={showcase.id} showcase={showcase} />
        ))}
      </div>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────
export default function NetworkPage() {
  const { checkAccess } = usePlan();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2">
          <Globe className="h-6 w-6 text-orange-600" />
          <h1 className="text-2xl font-bold text-gray-900">Paylaşım Ağı</h1>
        </div>
        <p className="mt-1 text-gray-500">
          Vitrin sayfanızı oluşturun, ilanlarınızı paylaşın ve diğer ofislerle
          ağ kurun.
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="showcase">
        <TabsList>
          <TabsTrigger value="showcase" className="gap-1.5">
            <Store className="h-4 w-4" />
            Vitrin Yönetimi
          </TabsTrigger>
          <TabsTrigger value="network" className="gap-1.5">
            <Users className="h-4 w-4" />
            Paylaşım Ağı
            {!checkAccess('hasSharingNetwork') && <Lock className="ml-1 h-3 w-3 text-amber-500" />}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="showcase" className="mt-6">
          <ShowcaseManagement />
        </TabsContent>

        <TabsContent value="network" className="mt-6">
          <FeatureGate feature="hasSharingNetwork" featureName="Paylaşım Ağı" requiredPlan="pro">
            <SharingNetwork />
          </FeatureGate>
        </TabsContent>
      </Tabs>
    </div>
  );
}


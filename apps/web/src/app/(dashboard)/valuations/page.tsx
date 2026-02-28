"use client"

import * as React from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ValuationForm } from "@/components/valuation/ValuationForm"
import { ValuationHistory } from "@/components/valuation/ValuationHistory"

export default function ValuationsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <Tabs defaultValue="new" className="space-y-6">
        <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Değerlemelerim</h1>
            <TabsList>
                <TabsTrigger value="new">Yeni Değerleme</TabsTrigger>
                <TabsTrigger value="history">Geçmiş Değerlemeler</TabsTrigger>
            </TabsList>
        </div>
        
        <TabsContent value="new" className="mt-0">
          <ValuationForm />
        </TabsContent>
        
        <TabsContent value="history" className="mt-0">
          <ValuationHistory />
        </TabsContent>
      </Tabs>
    </div>
  )
}

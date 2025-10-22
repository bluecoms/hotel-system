<template>
  <PageShell title="Dashboard" icon="mdi-view-dashboard">
    <template #toolbar>
      <div class="toolbar-wrap">
        <div class="left row">
          <label class="lbl">Property</label>
          <v-select
            v-model="propertyCode"
            :items="propertyOptions"
            density="compact"
            hide-details
            style="max-width:150px"
          />

          <label class="lbl ml-3">Business Date</label>
          <v-btn icon="mdi-chevron-left" size="small" variant="text" @click="shiftDay(-1)" />
          <v-text-field
            v-model="bizDate"
            type="date"
            density="compact"
            hide-details
            style="max-width:160px"
          />
          <v-btn icon="mdi-chevron-right" size="small" variant="text" @click="shiftDay(1)" />
          <v-btn variant="tonal" size="small" @click="setToday">Today</v-btn>
        </div>

        <v-spacer />

        <div class="right row">
          <v-chip :color="closing.status === 'CLOSED' ? 'green' : 'orange'" label>
            <template v-if="closing.status === 'CLOSED'">CLOSED</template>
            <template v-else>OPEN · {{ closing.done }}/{{ closing.total }}</template>
          </v-chip>
          <div class="progress-wrap">
            <v-progress-linear
              :model-value="closingPercent"
              height="8"
              rounded
              color="primary"
            />
          </div>
          <v-btn color="primary" size="small" @click="fetchAll">Refresh</v-btn>
        </div>
      </div>
    </template>

    <div class="top-grid">
      <KpiCard title="Room Only" :value="kpi?.room_only_amount ?? 0" prefix="₩" />
      <KpiCard title="Package" :value="kpi?.package_amount ?? 0" prefix="₩" />
      <KpiCard title="Other" :value="kpi?.other_amount ?? 0" prefix="₩" />
      <KpiCard title="Total" :value="totalAmount" prefix="₩" />
    </div>

    <v-card class="panel">
      <v-card-title class="d-flex align-center justify-space-between">
        <h3 class="text-h6 font-weight-bold">Bank & Cash</h3>
      </v-card-title>
      <v-card-text>
        <BankLedgerSummary
          :property-code="propertyCode"
          :default-date="bizDate"
          :default-account="'NH-301-xxxx'"
        />
      </v-card-text>
    </v-card>

    <div class="grid-2">
      <ComingSoonOverlay label="Inventory v1 예정">
        <v-card class="panel">
          <v-card-title><h3 class="text-h6 font-weight-bold">재고 요약</h3></v-card-title>
          <v-card-text><SkeletonCard :lines="4" /></v-card-text>
        </v-card>
      </ComingSoonOverlay>

      <ComingSoonOverlay label="근태 v1 예정">
        <v-card class="panel">
          <v-card-title><h3 class="text-h6 font-weight-bold">근태 요약</h3></v-card-title>
          <v-card-text><SkeletonCard :lines="4" /></v-card-text>
        </v-card>
      </ComingSoonOverlay>
    </div>
  </PageShell>
</template>

<style scoped>
.toolbar-wrap {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
}
.lbl {
  font-size: 0.9rem;
  color: #6b7280;
  font-weight: 500;
}
.ml-3 {
  margin-left: 12px;
}
.progress-wrap {
  width: 120px;
  margin-left: 8px;
}
.top-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}
.panel {
  border: 1px solid var(--surface-3, #e8e8e8);
  border-radius: 12px;
  background: var(--surface-1, #fff);
  padding: 12px;
}
</style>

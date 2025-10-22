<!-- src/views/Ota.vue -->
<template>
  <v-container class="py-6" style="max-width:1200px">
    <div class="toolbar-sticky ota-bar">
      <div class="bar-left">
        <h2 class="text-h6 title-text">OTA 관리</h2>
      </div>
    </div>

    <v-tabs v-model="tab" color="primary" class="mb-4">
      <v-tab value="sales">매출 요약</v-tab>
      <v-tab value="alias">채널 별칭</v-tab>
      <v-tab value="fees">채널 수수료</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- 매출 요약 -->
      <v-window-item value="sales">
        <v-card class="mb-4">
          <v-card-text>
            <div class="ctl-row">
              <v-text-field
                v-model="from"
                label="시작일 (YYYY-MM-DD)"
                variant="outlined"
                density="comfortable"
                class="date-input"
                hide-details
              />
              <v-text-field
                v-model="to"
                label="종료일 (YYYY-MM-DD)"
                variant="outlined"
                density="comfortable"
                class="date-input"
                hide-details
              />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-database-refresh" @click="syncAndLoad">
                불러오기
              </v-btn>

              <v-btn
                variant="tonal"
                class="btn-ctl"
                prepend-icon="mdi-download"
                @click="exportSalesCsv"
                :disabled="!sales.rows.length"
              >
                CSV 내보내기
              </v-btn>

              <v-spacer />

              <v-chip variant="tonal" class="meta-chip">
                미분류: 총액 {{ fmtMoney(sales.unknown.gross) }} / 건수 {{ sales.unknown.count }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th>채널</th>
              <th class="text-right">총액</th>
              <th class="text-right">수수료 %</th>
              <th class="text-right">수수료</th>
              <th class="text-right">순액</th>
              <th class="text-right">건수</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in sales.rows" :key="r.channel">
              <td>{{ r.channel }}</td>
              <td class="text-right">{{ fmtMoney(r.gross) }}</td>
              <td class="text-right">{{ r.fee_pct ?? 0 }}</td>
              <td class="text-right">
                {{ fmtMoney(r.fee_amount ?? (r.gross * (Number(r.fee_pct || 0)/100))) }}
              </td>
              <td class="text-right">
                {{ fmtMoney(r.net ?? (r.gross - (r.fee_amount ?? (r.gross * (Number(r.fee_pct || 0)/100))))) }}
              </td>
              <td class="text-right">{{ r.count || 0 }}</td>
            </tr>
            <tr v-if="!sales.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">데이터가 없습니다</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td class="text-right"><strong>합계</strong></td>
              <td class="text-right"><strong>{{ fmtMoney(sales.total.gross) }}</strong></td>
              <td></td>
              <td></td>
              <td class="text-right"><strong>{{ fmtMoney(sales.total.net) }}</strong></td>
              <td></td>
            </tr>
          </tfoot>
        </v-table>
      </v-window-item>

      <!-- 채널 별칭 -->
      <v-window-item value="alias">
        <v-card class="mb-4">
          <v-card-text>
            <div class="ctl-row">
              <v-text-field
                v-model="alias.q"
                label="검색"
                variant="outlined"
                density="comfortable"
                class="search-input"
                hide-details
                @keyup.enter="loadAlias(1)"
              />
              <v-select
                :items="activeFilterItems"
                v-model="alias.active"
                label="상태"
                density="comfortable"
                variant="outlined"
                class="mini-select"
                hide-details
              />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-magnify" @click="loadAlias(1)">검색</v-btn>
              <v-spacer />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-plus" @click="openAliasCreate">새 별칭</v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width:80px">ID</th>
              <th>Pattern (k)</th>
              <th>Canonical (v)</th>
              <th class="text-right" style="width:120px">Weight</th>
              <th style="width:120px">Active</th>
              <th style="width:200px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in alias.rows" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.k }}</td>
              <td>{{ r.v }}</td>
              <td class="text-right">{{ r.weight }}</td>
              <td>
                <v-chip :color="r.is_active ? 'success' : 'grey'" size="small" label>{{ r.is_active ? 'Y' : 'N' }}</v-chip>
              </td>
              <td class="d-flex" style="gap:8px">
                <v-btn size="small" variant="text" @click="openAliasEdit(r)">Edit</v-btn>
                <v-btn size="small" variant="tonal" color="red" @click="delKeyword(r, GROUP_ALIAS)">Delete</v-btn>
              </td>
            </tr>
            <tr v-if="!alias.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">항목이 없습니다</td>
            </tr>
          </tbody>
        </v-table>

        <div class="d-flex justify-center my-4">
          <v-pagination v-model="alias.page" :length="alias.pages" @update:modelValue="loadAlias"/>
        </div>
      </v-window-item>

      <!-- 수수료 -->
      <v-window-item value="fees">
        <v-card class="mb-4">
          <v-card-text>
            <div class="ctl-row">
              <v-text-field
                v-model="fee.q"
                label="검색"
                variant="outlined"
                density="comfortable"
                class="search-input"
                hide-details
                @keyup.enter="loadFee(1)"
              />
              <v-select
                :items="activeFilterItems"
                v-model="fee.active"
                label="상태"
                density="comfortable"
                variant="outlined"
                class="mini-select"
                hide-details
              />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-magnify" @click="loadFee(1)">검색</v-btn>
              <v-spacer />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-plus" @click="openFeeCreate">새 수수료</v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width:80px">ID</th>
              <th>Channel (k)</th>
              <th class="text-right" style="width:140px">Fee % (v)</th>
              <th class="text-right" style="width:120px">Weight</th>
              <th style="width:120px">Active</th>
              <th style="width:200px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in fee.rows" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.k }}</td>
              <td class="text-right">{{ r.v }}</td>
              <td class="text-right">{{ r.weight }}</td>
              <td>
                <v-chip :color="r.is_active ? 'success' : 'grey'" size="small" label>{{ r.is_active ? 'Y' : 'N' }}</v-chip>
              </td>
              <td class="d-flex" style="gap:8px">
                <v-btn size="small" variant="text" @click="openFeeEdit(r)">Edit</v-btn>
                <v-btn size="small" variant="tonal" color="red" @click="delKeyword(r, GROUP_FEE)">Delete</v-btn>
              </td>
            </tr>
            <tr v-if="!fee.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">항목이 없습니다</td>
            </tr>
          </tbody>
        </v-table>

        <div class="d-flex justify-center my-4">
          <v-pagination v-model="fee.page" :length="fee.pages" @update:modelValue="loadFee"/>
        </div>
      </v-window-item>
    </v-window>

    <!-- Alias Dialog -->
    <v-dialog v-model="dlgAlias" max-width="520">
      <v-card>
        <v-card-title>{{ aliasForm.id ? 'Edit Alias' : 'New Alias' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="aliasForm.k" label="Pattern (정규식/파이프 구분 등 자유)" />
          <v-text-field v-model="aliasForm.v" label="Canonical (표준 채널명, 예: agoda)" />
          <div class="d-flex" style="gap:12px">
            <v-text-field v-model.number="aliasForm.weight" label="Weight" type="number" style="max-width:160px"/>
            <v-switch v-model="aliasForm.is_active" label="Active" inset />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn variant="text" @click="dlgAlias=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveAlias">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fee Dialog -->
    <v-dialog v-model="dlgFee" max-width="520">
      <v-card>
        <v-card-title>{{ feeForm.id ? 'Edit Fee' : 'New Fee' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="feeForm.k" label="Channel (표준 채널명, 예: agoda)" />
          <v-text-field v-model="feeForm.v" label="Fee % (숫자, 예: 12.5)" type="number" />
          <div class="d-flex" style="gap:12px">
            <v-text-field v-model.number="feeForm.weight" label="Weight" type="number" style="max-width:160px"/>
            <v-switch v-model="feeForm.is_active" label="Active" inset />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn variant="text" @click="dlgFee=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveFee">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

const { success, error } = useToast()

// 탭 및 다이얼로그 상태
const tab = ref<'sales'|'alias'|'fees'>('sales')
const dlgAlias = ref(false)
const dlgFee = ref(false)

// 매출 탭
const from = ref('')
const to = ref('')
const sales = ref({ rows: [] as any[], total: { gross: 0, net: 0 }, unknown: { gross: 0, count: 0 } })

function fmtMoney(v: number) {
  return (v || 0).toLocaleString()
}
async function syncAndLoad() {
  // TODO: 실제 API 연결
  success('매출 데이터 불러오기 완료 (샘플)')
}
function exportSalesCsv() {
  window.open(`/api/reports/ota-sales-export?from=${from.value}&to=${to.value}`, '_blank')
}

// Alias 탭
const alias = ref({ q: '', active: 'ALL', rows: [] as any[], page: 1, pages: 1 })
const aliasForm = ref({ id: null, k: '', v: '', weight: 100, is_active: true })
const activeFilterItems = ['ALL', 'ACTIVE', 'INACTIVE']
function loadAlias() { /* TODO */ }
function openAliasCreate() { aliasForm.value = { id: null, k: '', v: '', weight: 100, is_active: true }; dlgAlias.value = true }
function openAliasEdit(r: any) { aliasForm.value = { ...r }; dlgAlias.value = true }
function saveAlias() { success('Alias 저장 (샘플)'); dlgAlias.value = false }

// Fee 탭
const fee = ref({ q: '', active: 'ALL', rows: [] as any[], page: 1, pages: 1 })
const feeForm = ref({ id: null, k: '', v: '', weight: 100, is_active: true })
function loadFee() { /* TODO */ }
function openFeeCreate() { feeForm.value = { id: null, k: '', v: '', weight: 100, is_active: true }; dlgFee.value = true }
function openFeeEdit(r: any) { feeForm.value = { ...r }; dlgFee.value = true }
function saveFee() { success('Fee 저장 (샘플)'); dlgFee.value = false }

// 삭제 더미 함수
function delKeyword(r: any, group: string) {
  error(`삭제: ${r.k || r.id} (${group})`)
}

const GROUP_ALIAS = 'alias'
const GROUP_FEE = 'fee'
</script>

<style scoped>
.ota-bar{position:sticky;top:56px;z-index:5;display:grid;grid-template-columns:1fr auto;align-items:center;gap:12px;padding:10px 12px;background:rgb(var(--v-theme-surface));box-shadow:0 2px 10px rgba(16,24,40,.06);border-radius:12px;margin-bottom:12px}
.title-text{font-weight:700;line-height:40px}
.ctl-row{display:flex;flex-wrap:wrap;align-items:center;gap:10px}
.date-input{width:220px;--ctl-h:40px}
.date-input :deep(.v-field){height:var(--ctl-h)}
.btn-ctl{height:40px;text-transform:none;font-weight:500}
.search-input{width:260px}
.mini-select{width:140px}
.meta-chip{height:32px}
</style>

<!-- ============================================================================
# src/views/Ota.vue
# Hotel Admin — OTA 관리화면 (v2025-10-17 Stable)
# ------------------------------------------------------------------------------
# 목적:
#   • OTA(온라인 여행사) 관련 데이터 정제·관리 화면
#   • 탭 구조로 구성: 매출 요약 / 채널 별칭 / 채널 수수료
#   • 백엔드 연결 포인트:
#       - GET  /api/ota/summary?business_date=YYYY-MM-DD  → 매출 요약
#       - GET  /api/ota/channels, /api/ota/commissions    → 별칭/수수료 관리
#   • “매출 요약” 탭은 OTAOrder 데이터를 기반으로 일자별 집계
#   • “별칭/수수료” 탭은 Refine(정제) 데이터 관리용 CRUD 탭
# ------------------------------------------------------------------------------
# 주의:
#   - CSV 내보내기용 /api/reports/ota-sales-export 엔드포인트는 추후 리포트용.
#   - 현재 버전은 Refine 단계용, Dashboard용 API는 별도 구성 예정.
# ============================================================================ -->
<template>
  <v-container class="py-6" style="max-width:1200px">
    <!-- 상단 툴바 -->
    <div class="toolbar-sticky ota-bar">
      <div class="bar-left">
        <h2 class="text-h6 title-text">OTA 관리</h2>
      </div>
    </div>

    <!-- 탭 -->
    <v-tabs v-model="tab" color="primary" class="mb-4">
      <v-tab value="sales">매출 요약</v-tab>
      <v-tab value="alias">채널 별칭</v-tab>
      <v-tab value="fees">채널 수수료</v-tab>
    </v-tabs>

    <!-- 탭 콘텐츠 -->
    <v-window v-model="tab">
      <!-- ───────────── 매출 요약 탭 ───────────── -->
      <v-window-item value="sales">
        <v-card class="mb-4">
          <v-card-text>
            <div class="ctl-row">
              <v-text-field
                v-model="bizDate"
                label="기준일 (YYYY-MM-DD)"
                variant="outlined"
                density="comfortable"
                class="date-input"
                hide-details
              />
              <v-btn
                color="primary"
                class="btn-ctl"
                prepend-icon="mdi-database-refresh"
                @click="loadSummary"
              >불러오기</v-btn>

              <v-btn
                variant="tonal"
                class="btn-ctl"
                prepend-icon="mdi-download"
                @click="exportSalesCsv"
                :disabled="!sales.rows.length"
              >CSV 내보내기</v-btn>

              <v-spacer />

              <v-chip variant="tonal" class="meta-chip">
                미분류: 총액 {{ fmtMoney(sales.unknown.gross) }} /
                건수 {{ sales.unknown.count }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>

        <!-- 매출 테이블 -->
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
              <td class="text-right">{{ fmtMoney(r.fee_amount) }}</td>
              <td class="text-right">{{ fmtMoney(r.net) }}</td>
              <td class="text-right">{{ r.count || 0 }}</td>
            </tr>
            <tr v-if="!sales.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">
                데이터가 없습니다
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td class="text-right"><strong>합계</strong></td>
              <td class="text-right">
                <strong>{{ fmtMoney(sales.total.gross) }}</strong>
              </td>
              <td></td><td></td>
              <td class="text-right">
                <strong>{{ fmtMoney(sales.total.net) }}</strong>
              </td>
              <td></td>
            </tr>
          </tfoot>
        </v-table>
      </v-window-item>

      <!-- ───────────── 채널 별칭 탭 ───────────── -->
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
                @keyup.enter="loadAlias"
              />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-magnify" @click="loadAlias">검색</v-btn>
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
                <v-chip :color="r.is_active ? 'success' : 'grey'" size="small" label>
                  {{ r.is_active ? 'Y' : 'N' }}
                </v-chip>
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
      </v-window-item>

      <!-- ───────────── 수수료 탭 ───────────── -->
      <v-window-item value="fees">
        <v-card class="mb-4">
          <v-card-text>
            <div class="ctl-row">
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-refresh" @click="loadFee">새로고침</v-btn>
              <v-spacer />
              <v-btn color="primary" class="btn-ctl" prepend-icon="mdi-plus" @click="openFeeCreate">새 수수료</v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width:80px">ID</th>
              <th>Channel</th>
              <th class="text-right" style="width:140px">Fee %</th>
              <th>Note</th>
              <th style="width:200px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in fee.rows" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.channel }}</td>
              <td class="text-right">{{ r.rate }}</td>
              <td>{{ r.note }}</td>
              <td class="d-flex" style="gap:8px">
                <v-btn size="small" variant="text" @click="openFeeEdit(r)">Edit</v-btn>
              </td>
            </tr>
            <tr v-if="!fee.rows.length">
              <td colspan="5" class="text-center text-medium-emphasis py-6">항목이 없습니다</td>
            </tr>
          </tbody>
        </v-table>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

const { success, error } = useToast()
const tab = ref<'sales' | 'alias' | 'fees'>('sales')

// ───────────── 매출 요약
const bizDate = ref('')
const sales = ref({ rows: [] as any[], total: { gross: 0, net: 0 }, unknown: { gross: 0, count: 0 } })
function fmtMoney(v: number) { return (v || 0).toLocaleString() }

async function loadSummary() {
  if (!bizDate.value) return error('기준일을 입력하세요')
  try {
    const res: any = await http.get(`/ota/summary?business_date=${bizDate.value}`)
    sales.value = {
      rows: res.items || [],
      total: res.total || { gross: 0, net: 0 },
      unknown: res.unknown || { gross: 0, count: 0 },
    }
    success('매출 요약 불러오기 완료')
  } catch (e: any) {
    error(`불러오기 실패: ${e.message || e}`)
  }
}

function exportSalesCsv() {
  if (!bizDate.value) return
  window.open(`/api/reports/ota-sales-export?business_date=${bizDate.value}`, '_blank')
}

// ───────────── 별칭/수수료 (Refine용 더미)
const alias = ref({ q: '', rows: [] as any[] })
const aliasForm = ref({ id: null, k: '', v: '', weight: 100, is_active: true })
function loadAlias() { success('Alias 불러오기 (샘플)') }
function openAliasCreate() { dlgAlias.value = true }
function openAliasEdit(r: any) { aliasForm.value = { ...r }; dlgAlias.value = true }
function delKeyword(r: any, g: string) { error(`삭제: ${r.k}`) }

const fee = ref({ rows: [] as any[] })
function loadFee() { success('수수료 목록 불러오기 (샘플)') }
function openFeeCreate() { success('새 수수료 생성 (샘플)') }
function openFeeEdit(r: any) { success(`수정: ${r.channel}`) }

const dlgAlias = ref(false)
</script>

<style scoped>
.ota-bar {
  position: sticky;
  top: 56px;
  z-index: 5;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 2px 10px rgba(16, 24, 40, .06);
  border-radius: 12px;
  margin-bottom: 12px;
}
.title-text { font-weight: 700; line-height: 40px }
.ctl-row { display:flex; flex-wrap:wrap; align-items:center; gap:10px }
.date-input { width:220px; --ctl-h:40px }
.date-input :deep(.v-field){ height:var(--ctl-h) }
.btn-ctl{ height:40px; text-transform:none; font-weight:500 }
.meta-chip{ height:32px }
</style>
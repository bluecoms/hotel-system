<!--# src/ui/components/common/DialogLinkAccount.vue (계좌 연결 다이얼로그)
───────────────────────────────────────────────────────────────
Version : 3.2.0  |  Date : 2025-10-16  |  Owner : Hotel Admin (Finance)
Purpose : 특정 데이터셋(예: 지출, 매출, 정산 등)에 연결할 은행계좌를
          선택하거나 수동 등록할 수 있는 공통 다이얼로그.

[핵심 기능]
- 계좌 목록 조회 (/api/bank/accounts)
- 목록에서 선택 또는 수동 등록 모드 전환 (allowCustom)
- 신규 등록 시 POST /api/bank/accounts/link 호출
- 연결 완료 시 linked 이벤트 emit (code, account, custom)
- property_code, dataset, bizDate를 함께 전송하여 연결 맥락 유지

[API & 계약]
- GET  /api/bank/accounts         → { items[], total }
- POST /api/bank/accounts/link    → { ok: true, code, ... }
- 인증: X-Internal-Token (필수)
- 파라미터: property_code, dataset, business_date, code, bank, account_no 등

[UI 구성]
- 상단: Property / Dataset / Date / 현재 연결 표시
- 검색창 + 새로고침 + 수동등록 스위치
- 목록 모드: v-data-table (선택 시 emit)
- 수동 모드: 신규 계좌 입력폼

[변경 이력]
- 3.2.0: 주석 블록 추가, 한글화, UX/토스트 메시지 통일
- 3.1.0: allowCustom 스위치 추가, http.ts 적용, mask 포맷 개선
-->
<template>
  <v-dialog
    :model-value="open"
    max-width="860"
    scrollable
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card>
      <!-- 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-bank" class="mr-1" />
          계좌 연결
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <!-- 본문 -->
      <v-card-text>
        <!-- 상단 정보칩 -->
        <div class="row mb-3">
          <v-chip size="small" variant="outlined">지점: {{ propertyCode }}</v-chip>
          <v-chip size="small" variant="tonal" v-if="dataset">데이터셋: {{ dataset }}</v-chip>
          <v-chip size="small" variant="tonal" v-if="bizDate">{{ bizDate }}</v-chip>
          <v-chip v-if="currentCode" size="small" variant="flat" color="primary">
            현재 연결: {{ currentCode }}
          </v-chip>
        </div>

        <!-- 검색 및 모드 전환 -->
        <v-row class="mb-2" align="center">
          <v-col cols="12" md="6">
            <v-text-field
              v-model="query"
              prepend-inner-icon="mdi-magnify"
              label="검색 (은행/계좌/코드/별칭)"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              @keydown.enter="debouncedLoad()"
            />
          </v-col>
          <v-col cols="12" md="6" class="d-flex justify-end align-center">
            <v-btn
              class="mr-2"
              variant="tonal"
              prepend-icon="mdi-refresh"
              :loading="loading"
              @click="load"
            >
              새로고침
            </v-btn>
            <v-switch
              v-if="allowCustom"
              v-model="useCustom"
              inset
              color="primary"
              hide-details
              :label="useCustom ? '수동 등록' : '목록에서 선택'"
            />
          </v-col>
        </v-row>

        <!-- 목록 모드 -->
        <v-expand-transition>
          <div v-if="!useCustom">
            <v-skeleton-loader v-if="loading" type="table" class="my-2" />
            <template v-else>
              <v-data-table
                :headers="headers"
                :items="rows"
                :items-per-page="perPage"
                v-model:page="page"
                :loading="loading"
                density="comfortable"
                hover
                fixed-header
                height="360"
                class="elevation-1"
                :no-data-text="noDataText"
                @click:row="onPick"
              >
                <template #item._index="{ index }">
                  {{ (page - 1) * perPage + index + 1 }}
                </template>
                <template #item.account_mask="{ item }">
                  <span class="mono">{{ mask(item.account_no) }}</span>
                </template>
                <template #item._action="{ item }">
                  <v-btn
                    size="small"
                    variant="text"
                    prepend-icon="mdi-link-variant"
                    @click.stop="onPick(item)"
                  >
                    선택
                  </v-btn>
                </template>
                <template #no-data>
                  <StateBlock :message="noDataText" />
                </template>
                <template #bottom>
                  <div class="d-flex justify-end px-2 py-2">
                    <v-pagination v-model="page" :length="pages" :total-visible="7" />
                  </div>
                </template>
              </v-data-table>
            </template>
          </div>
        </v-expand-transition>

        <!-- 수동 등록 모드 -->
        <v-expand-transition>
          <div v-if="useCustom" class="panel mt-2 pa-3">
            <v-row dense>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="custom.code"
                  label="계좌 코드(고유)"
                  :rules="[req]"
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field v-model="custom.alias" label="별칭" hide-details="auto" />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="custom.bank"
                  label="은행명"
                  :rules="[req]"
                  hide-details="auto"
                />
              </v-col>

              <v-col cols="12" md="8">
                <v-text-field
                  v-model="custom.account_no"
                  label="계좌번호"
                  :rules="[req]"
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field v-model="custom.owner" label="예금주" hide-details="auto" />
              </v-col>

              <v-col cols="12">
                <v-text-field v-model="custom.memo" label="메모" hide-details="auto" />
              </v-col>
            </v-row>
          </div>
        </v-expand-transition>
      </v-card-text>

      <v-divider />

      <!-- 액션 -->
      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="emit('update:open', false)">닫기</v-btn>
        <v-btn
          color="primary"
          :loading="submitting"
          :disabled="linkDisabled"
          prepend-icon="mdi-link"
          @click="onLink"
        >
          연결
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

type BankAccount = {
  code: string
  alias?: string
  bank?: string
  account_no?: string
  owner?: string
  memo?: string
  updated_at?: string
}

/** 부모 → 전달 props 정의 */
const props = defineProps<{
  open: boolean
  propertyCode: string
  dataset?: string
  bizDate?: string
  currentCode?: string | null
  allowCustom?: boolean
  fetchUrl?: string
  linkUrl?: string
}>()

/** 부모로 이벤트 emit */
const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'linked', payload: { code: string; account?: BankAccount; custom?: boolean }): void
}>()

const { error, success } = useToast()

/** 테이블 헤더 정의 */
const headers = [
  { title: '#', key: '_index', width: 64, align: 'center' },
  { title: '코드', key: 'code', width: 160, align: 'start' },
  { title: '별칭', key: 'alias', align: 'start' },
  { title: '은행', key: 'bank', width: 120, align: 'start' },
  { title: '계좌', key: 'account_mask', width: 200, align: 'center' },
  { title: '예금주', key: 'owner', width: 120, align: 'start' },
  { title: '', key: '_action', width: 100, align: 'end', sortable: false },
]

/** 내부 상태 */
const dialogOpen = computed(() => props.open)
const propertyCode = computed(() => props.propertyCode)
const dataset = computed(() => props.dataset ?? '')
const bizDate = computed(() => props.bizDate ?? '')
const allowCustom = computed(() => props.allowCustom !== false)

const loading = ref(false)
const submitting = ref(false)
const query = ref('')
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const rows = ref<BankAccount[]>([])
const pages = computed(() => Math.max(1, Math.ceil(total.value / perPage.value)))
const noDataText = '등록된 계좌가 없습니다.'

const useCustom = ref(false)
const custom = reactive({ code: '', bank: '', account_no: '', alias: '', owner: '', memo: '' })
const req = (v: any) => !!String(v ?? '').trim() || '입력값을 확인해주세요.'

/** API 기본경로 */
const fetchUrl = computed(() => props.fetchUrl || `/api/bank/accounts`)
const linkUrl = computed(() => props.linkUrl || `/api/bank/accounts/link`)

/** 계좌번호 마스킹 */
function mask(v?: string) {
  if (!v) return '-'
  const s = v.replace(/\s+/g, '')
  return s.length <= 6 ? s : `${s.slice(0, 3)}-****-****-${s.slice(-3)}`
}

/** 계좌 목록 로드 */
async function load() {
  try {
    loading.value = true
    const qs = http.qs({
      property_code: propertyCode.value,
      q: query.value || undefined,
      page: page.value,
      size: perPage.value,
    })
    const res: any = await http.get(`${fetchUrl.value}${qs}`)
    const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
    rows.value = items
    total.value = Number(res?.total ?? items.length ?? 0)
  } catch (e: any) {
    error(e?.message || '계좌 목록을 불러오지 못했습니다.')
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** 검색 지연 로드 */
const debouncedLoad = (() => {
  let t: any
  return () => {
    clearTimeout(t)
    t = setTimeout(() => {
      page.value = 1
      load()
    }, 180)
  }
})()

/** 선택 시 연결 처리 */
function onPick(item: BankAccount) {
  emit('linked', { code: item.code, account: item, custom: false })
  success('계좌가 연결되었습니다.')
  emit('update:open', false)
}

/** 수동 등록 입력 검증 */
const linkDisabled = computed(() => {
  if (!useCustom.value) return false
  return !custom.code || !custom.bank || !custom.account_no
})

/** 수동 등록 저장 */
async function onLink() {
  if (!useCustom.value) {
    error('목록에서 항목을 선택하세요.')
    return
  }
  try {
    submitting.value = true
    const payload = {
      property_code: propertyCode.value,
      dataset: dataset.value || undefined,
      business_date: bizDate.value || undefined,
      code: custom.code,
      alias: custom.alias || undefined,
      bank: custom.bank,
      account_no: custom.account_no,
      owner: custom.owner || undefined,
      memo: custom.memo || undefined,
    }
    await http.post(linkUrl.value, payload)
    emit('linked', { code: custom.code, account: { ...custom }, custom: true })
    success('계좌가 연결되었습니다.')
    emit('update:open', false)
    load() // 연결 후 목록 갱신
  } catch (e: any) {
    error(e?.message || '연결 실패')
  } finally {
    submitting.value = false
  }
}

/** 반응형 로드 제어 */
watch(page, load)
watch(query, debouncedLoad)
watch(dialogOpen, (v) => {
  if (v) {
    query.value = ''
    page.value = 1
    load()
  }
})

onMounted(() => {
  if (dialogOpen.value) load()
})
</script>

<style scoped>
.row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
}
</style>

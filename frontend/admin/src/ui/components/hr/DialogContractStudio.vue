<!-- ============================================================================
# File      : src/ui/components/hr/DialogContractStudio.vue
# Version   : 2025-11-10 · v2.0 (SSOT Final · Full Commented Edition)
# Purpose   : Hotel Admin — 계약서 작성/확정 다이얼로그
# ----------------------------------------------------------------------------
# 목적:
#   • 계약서 템플릿(iframe)에 직원 정보 자동 주입
#   • 인쇄 후 자동으로 계약 확정(activate)
#   • afterprint + fallback(3초) 으로 확정 안정성 확보
# ----------------------------------------------------------------------------
# 설계 원칙:
#   ✅ iframe postMessage 기반 데이터 주입 (3회 브로드캐스트)
#   ✅ append-only 구조 / activate 로직 서버 단위 확정
#   ✅ saving 플래그로 중복 클릭 방지
#   ✅ 주민등록번호 → 생년월일 변환 (mask 기반)
# ----------------------------------------------------------------------------
# 연계:
#   • EmployeesApi.getEmployee()   → 직원 기본정보 로드
#   • ContractsApi.activate()      → 계약 확정 처리
#   • HTML Template: /contracts/ocean-contract-v1.5.html
# ============================================================================ -->
<template>
  <v-dialog
    :model-value="open"
    max-width="1200"
    scrollable
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-2xl">
      <!-- ▣ 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between py-3">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-file-document-edit-outline" class="mr-1" />
          <div>
            <div class="text-subtitle-1 font-weight-bold">근로계약 작성</div>
            <div class="text-caption text-grey-darken-1">
              인쇄용 템플릿 v1.5 (iframe) · <b>월급형 전용</b>
            </div>
          </div>
        </div>
      </v-card-title>

      <v-divider />

      <!-- ▣ 직원 요약 정보 -->
      <v-card-text class="px-5 py-3">
        <v-row dense align="center">
          <v-col cols="12" md="9">
            <div class="d-flex flex-column">
              <div class="text-body-1 font-weight-bold">
                {{ empContext.name || '직원' }}
                <span v-if="empContext.emp_no">({{ empContext.emp_no }})</span>
              </div>
              <div class="text-caption text-grey-darken-1 mt-1">
                {{ empContext.dept_name || '-' }} · {{ empContext.title_name || '-' }}
              </div>
              <div class="text-caption text-grey-darken-2 mt-1">
                계약기간:
                <span class="font-weight-medium">{{ period.start || '-' }}</span>
                ~
                <span class="font-weight-medium">{{ period.end || '진행중' }}</span>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-card-text>

      <v-divider />

      <!-- ▣ 본문 (계약서 iframe) -->
      <v-card-text class="p-0">
        <div class="iframe-wrap">
          <iframe
            ref="iframeRef"
            :src="iframeUrl"
            class="contract-iframe"
            title="계약서 템플릿"
            @load="onIframeLoad"
          />
        </div>
      </v-card-text>

      <v-divider />

      <!-- ▣ 푸터 (닫기 / 인쇄·확정 버튼) -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" @click="emit('update:open', false)">닫기</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-printer"
          :disabled="!employeeId || saving"
          :loading="saving"
          @click="onPrintAndActivate"
        >
          인쇄
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ============================================================================
# Script Summary — 계약서 작성 & 확정 로직
# ----------------------------------------------------------------------------
# 구성:
#   • props.open      : 다이얼로그 표시 여부
#   • props.contract  : 계약 데이터 (id, emp_id, 기간 등)
#   • Employees API   : 직원 기본정보 로드
#   • iframe postMessage : 템플릿 데이터 주입
#   • afterprint 이벤트 : 인쇄 완료 후 activate() 실행
# ============================================================================ */
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as ContractsApi from '@/services/contracts'

/* ───────── Props / Emits ───────── */
const props = defineProps<{
  open: boolean
  contract?: {
    id: number
    employee_id: number
    start_date?: string | null
    end_date?: string | null
    salary?: number | null
    meta?: Record<string, any> | null
  }
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'saved'): void
}>()

const { success, error } = useToast()

/* ───────── 상태 정의 ───────── */
const employeeId = ref<number | null>(null)
const empContext = ref({
  name: '',
  emp_no: '',
  dept_name: '',
  title_name: '',
  birth: '',
  phone: '',
  address: '',
  account: '',
  salary: null as number | null,
})
const period = ref<{ start: string; end: string | null }>({ start: '', end: null })
const iframeReady = ref(false)
const contextReady = ref(false)
const saving = ref(false)

/* ───────── 유틸: 주민등록번호 → 생년월일 변환 ───────── */
function rrnToBirth(rrn?: string): string {
  if (!rrn) return ''
  const clean = rrn.replace(/[^0-9]/g, '')
  if (clean.length < 6) return ''
  const yy = parseInt(clean.slice(0, 2))
  const mm = clean.slice(2, 4)
  const dd = clean.slice(4, 6)
  const century = yy <= 25 ? '20' : '19'
  return `${century}${yy.toString().padStart(2, '0')}-${mm}-${dd}`
}

/* ───────── iframe 데이터 브로드캐스트 ─────────
   템플릿 측 수신 이벤트:
     - fill / fillForm / set
   초기화 타이밍 불일치 방지를 위해 3회(100·300·700ms) 전송
────────────────────────────────────────────── */
const iframeRef = ref<HTMLIFrameElement | null>(null)
function broadcastFill(p: any) {
  const win = iframeRef.value?.contentWindow
  if (!win) return
  win.postMessage({ type: 'fill', payload: p }, '*')
  win.postMessage({ type: 'fillForm', data: p }, '*')
  for (const [name, value] of Object.entries(p)) {
    win.postMessage({ type: 'set', name, value }, '*')
  }
}
function maybeFill() {
  if (!iframeReady.value || !contextReady.value) return
  const p = {
    name: empContext.value.name,
    emp_no: empContext.value.emp_no,
    dept_name: empContext.value.dept_name,
    title_name: empContext.value.title_name,
    birth: empContext.value.birth,
    phone: empContext.value.phone,
    address: empContext.value.address,
    account: empContext.value.account,
    salary: empContext.value.salary,
    start_date: period.value.start,
    end_date: period.value.end,
  }
  for (const delay of [100, 300, 700]) {
    setTimeout(() => broadcastFill(p), delay)
  }
}

/* ───────── 다이얼로그 오픈 → 직원 데이터 로드 ───────── */
watch(
  () => props.open,
  async (visible) => {
    if (!visible) return
    contextReady.value = false
    try {
      const c = props.contract
      if (!c?.employee_id) {
        error('계약 정보가 없습니다.')
        return
      }
      employeeId.value = c.employee_id

      const emp: any = await EmployeesApi.getEmployee(c.employee_id)
      empContext.value = {
        name: emp?.name ?? '',
        emp_no: emp?.emp_no ?? '',
        dept_name: emp?.dept_name ?? emp?.dept ?? '',
        title_name: emp?.title_name ?? emp?.title ?? '',
        birth: rrnToBirth(emp?.rrn_mask ?? emp?.birth_date),
        phone: emp?.phone ?? '',
        address: emp?.address ?? '',
        account: c?.meta?.account ?? emp?.account_mask ?? emp?.account ?? '',
        salary: c?.salary ?? null,
      }

      period.value.start = c.start_date || ''
      period.value.end = c.end_date || null

      contextReady.value = true
      maybeFill()
    } catch (e) {
      console.error('[Studio] employee load fail:', e)
      error('직원 정보를 불러오지 못했습니다.')
    }
  }
)

/* ───────── iframe 초기화 및 준비 이벤트 ───────── */
const iframeUrl = '/contracts/ocean-contract-v1.5.html'
function onIframeLoad() {
  iframeReady.value = true
  const win = iframeRef.value?.contentWindow
  if (!win) return
  win.postMessage({ type: 'init', template: 'MONTHLY' }, '*')
  win.postMessage({ type: 'switchTab', target: 'MONTHLY' }, '*')
  maybeFill()
}

/* ───────── postMessage 수신 처리 ───────── */
function onMessage(ev: MessageEvent) {
  const msg = ev.data
  if (!msg || typeof msg !== 'object') return
  if (msg.type === 'ready') {
    iframeReady.value = true
    maybeFill()
  }
}

/* ───────── 인쇄 & 계약 확정 로직 ─────────
   1) window.print() 호출
   2) afterprint 이벤트 → ContractsApi.activate()
   3) 3초 fallback 으로 안정적 확정 보장
────────────────────────────────────────────── */
async function onPrintAndActivate() {
  if (saving.value || !props.contract?.id) return
  const win = iframeRef.value?.contentWindow
  win?.focus()
  win?.print()

  saving.value = true
  const handler = async () => {
    window.removeEventListener('afterprint', handler)
    try {
      await ContractsApi.activate(props.contract!.id)
      success('계약이 확정되었습니다.')
      emit('saved')
    } catch (err) {
      console.error('[Studio] activate failed:', err)
      error('계약 확정 실패')
    } finally {
      saving.value = false
    }
  }

  window.addEventListener('afterprint', handler)
  setTimeout(() => { if (saving.value) handler() }, 3000)
}

/* ───────── 이벤트 등록/해제 ───────── */
onMounted(() => window.addEventListener('message', onMessage))
onBeforeUnmount(() => window.removeEventListener('message', onMessage))
</script>

<style scoped>
/* ============================================================================
# Style — 계약서 작성 뷰
# ----------------------------------------------------------------------------
# - iframe 영역은 밝은 배경과 상단 라운드 유지
# - 화면 높이 가변 대응 (scrollable dialog)
# ============================================================================
*/
.iframe-wrap { height: calc(100vh - 280px); background: #f8fafc; }
.contract-iframe {
  width: 100%;
  height: 100%;
  border: 0;
  background: #fff;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}
</style>

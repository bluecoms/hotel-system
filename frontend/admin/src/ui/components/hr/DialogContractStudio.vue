<!-- ============================================================================
  File    : /src/ui/components/hr/DialogContractStudio.vue
  Version : 1.8.4 (2025-10-20 Final Stable)
  Purpose : Hotel Admin — 계약서 작성·확정 다이얼로그 (HTML 템플릿 자동 주입)
  ------------------------------------------------------------------------------
  연결 백엔드:
    • GET    /api/employees/{id}            → 직원 상세정보 (계좌/부서/직책 포함)
    • PUT    /api/contracts/{id}/activate   → 계약 확정(활성화)
  주요 개선사항:
    ✅ 계약 확정 후 emit('saved') → 부모 reload() + 상위 emit('updated') 완전 동기화
    ✅ afterprint + fallback 병행 (PDF 저장 시에도 정상 처리)
    ✅ iframe 데이터 주입 안정화(maybeFill 3회 브로드캐스트)
    ✅ 에러 로그 및 Toast 중복 방지 정비
============================================================================ -->
<template>
  <v-dialog
    :model-value="open"
    max-width="1200"
    scrollable
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-2xl">
      <!-- ───── 헤더 ───── -->
      <v-card-title class="d-flex align-center justify-space-between py-3">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-file-document-edit-outline" class="mr-1" />
          <div>
            <div class="text-subtitle-1 font-weight-bold">근로계약 작성</div>
            <div class="text-caption text-grey-darken-1">
              인쇄용 템플릿 v1.5 (아이프레임) · <b>월급형 전용</b>
            </div>
          </div>
        </div>
      </v-card-title>

      <v-divider />

      <!-- ───── 직원 정보 섹션 ───── -->
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

      <!-- ───── 본문(아이프레임) ───── -->
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

      <!-- ───── 푸터(닫기 / 인쇄) ───── -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" @click="emit('update:open', false)">닫기</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-printer"
          :disabled="!employeeId"
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
/* ===========================================================================
  Script Logic — 직원/계약 데이터 자동 주입 + 인쇄 시 계약 활성화 처리
  ---------------------------------------------------------------------------
  • maybeFill(): iframeReady + contextReady 모두 true 시 주입
  • broadcastFill(): fill / fillForm / set 포맷 병행
  • onPrintAndActivate(): 인쇄 후 activate() 호출 → 계약 확정 + 부모 reload()
=========================================================================== */
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as ContractsApi from '@/services/contracts'

/** Props / Emits */
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

const emit = defineEmits<{ (e: 'update:open', v: boolean): void; (e: 'saved'): void }>()
const { success, error } = useToast()

/** 직원 컨텍스트 */
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

/** 계약 기간 */
const period = ref<{ start: string; end: string | null }>({ start: '', end: null })

/** 상태 플래그 */
const iframeReady = ref(false)
const contextReady = ref(false)

/** 주민번호 → 생년월일 */
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

/** 멀티포맷 브로드캐스트 */
function broadcastFill(p: any) {
  const win = iframeRef.value?.contentWindow
  if (!win) return
  win.postMessage({ type: 'fill', payload: p }, '*')
  win.postMessage({ type: 'fillForm', data: p }, '*')
  for (const [name, value] of Object.entries(p)) {
    win.postMessage({ type: 'set', name, value }, '*')
  }
}

/** 데이터 주입 */
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
  broadcastFill(p)
  setTimeout(() => broadcastFill(p), 200)
  setTimeout(() => broadcastFill(p), 500)
}

/** 계약 오픈 시 직원·계약정보 로드 */
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

/** iframe 통신 및 초기화 */
const iframeRef = ref<HTMLIFrameElement | null>(null)
const iframeUrl = '/contracts/ocean-contract-v1.5.html'

function onIframeLoad() {
  iframeReady.value = true
  const win = iframeRef.value?.contentWindow
  if (!win) return
  win.postMessage({ type: 'init', template: 'MONTHLY' }, '*')
  win.postMessage({ type: 'switchTab', target: 'MONTHLY' }, '*')
  maybeFill()
  setTimeout(maybeFill, 200)
  setTimeout(maybeFill, 500)
}

function onMessage(ev: MessageEvent) {
  const msg = ev.data
  if (!msg || typeof msg !== 'object') return
  if (msg.type === 'ready') {
    iframeReady.value = true
    maybeFill()
    setTimeout(maybeFill, 200)
  } else if (msg.type === 'contractSnapshotResult') {
    _pendingResolver?.(msg.data)
    _pendingResolver = null
  }
}

/** 스냅샷 요청 */
let _pendingResolver: ((v: any) => void) | null = null
function requestSnapshot(kind: 'MONTHLY'): Promise<any> {
  return new Promise((resolve) => {
    _pendingResolver = resolve
    iframeRef.value?.contentWindow?.postMessage({ type: 'getSnapshot', wanted: kind }, '*')
  })
}

/** 인쇄 + 계약 확정 처리 */
const saving = ref(false)
async function onPrintAndActivate() {
  const win = iframeRef.value?.contentWindow
  win?.focus()
  win?.print()
  if (!props.contract?.id) return

  try {
    saving.value = true
    const handler = async () => {
      window.removeEventListener('afterprint', handler)
      try {
        await ContractsApi.activate(props.contract.id)
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
    // fallback: afterprint 미발생 시
    setTimeout(() => { if (saving.value) handler() }, 3000)
  } catch (e) {
    saving.value = false
    console.error('[Studio] activate outer fail:', e)
    error('인쇄 처리 실패')
  }
}

/** 이벤트 등록/해제 */
onMounted(() => window.addEventListener('message', onMessage))
onBeforeUnmount(() => window.removeEventListener('message', onMessage))
</script>

<style scoped>
.iframe-wrap {
  height: calc(100vh - 280px);
  background: #f8fafc;
}
.contract-iframe {
  width: 100%;
  height: 100%;
  border: 0;
  background: #fff;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}
</style>

<!-- ============================================================================
# src/ui/components/closing/DatasetCard.vue
# Hotel Admin — DatasetCard (v2025.10 Final Stable · UX 2차 업그레이드)
# ----------------------------------------------------------------------------
# 목적
#   • 일자별 Dataset 업로드 "인라인 카드" (팝업 아님)
#   • 드래그&드롭 / 파일선택 / 드라이런 / (옵션) 파트 업로드 지원
#   • 업로드 성공 시 상위(Board.vue) refresh() 트리거 (emit: 'done')
#   • 업로드 이력(versions) 강조표시(가장 최근 v 강조) + 템플릿 미리보기/다운로드
#
# 백엔드 연동(SSOT Phase 3)
#   • POST /api/upload/{dataset}
#       - 필수: file(binary), business_date, property_code
#       - 선택: dry_run(1|0), split_by_date, source_kind, mode, part(무시 가능)
#   • GET  /api/upload/versions?dataset=...&property_code=...&business_date=...
#   • GET  /api/templates/{dataset}.csv   (템플릿 헤더 자동 생성)
#
# 주의
#   • 이 컴포넌트는 인라인 카드이며 v-dialog를 사용하지 않는다
#   • axios 금지, 반드시 fetch 기반 '@/services/http' 사용
#   • props.open 은 과거 호환을 위해 유지(표시에 관여 X)
#   • 'part' 필드는 레거시/확장 호환용 — 현재 백엔드에서 무시돼도 안전
# ============================================================================ -->
<template>
  <v-card class="upload-card pa-4 mb-6 rounded-xl">

    <!-- ───────────── 헤더 ───────────── -->
    <v-card-title class="d-flex align-center justify-space-between pb-2">
      <div class="d-flex align-center" style="gap:8px">
        <v-icon icon="mdi-upload" />
        <span class="text-subtitle-1 font-weight-bold">{{ headerTitle }}</span>
        <v-tooltip :text="headerHint">
          <template #activator="{ props }">
            <v-icon v-bind="props" icon="mdi-help-circle-outline" size="18" />
          </template>
        </v-tooltip>
      </div>

      <div class="d-flex align-center flex-wrap" style="gap:8px">
        <v-chip size="small" variant="outlined" class="font-weight-medium">
          {{ t('closing.property') }}: {{ propertyCode }}
        </v-chip>
        <v-chip size="small" variant="tonal" class="font-weight-medium">
          {{ bizDate }}
        </v-chip>

        <!-- 드라이런 토글(내부 상태) -->
        <v-tooltip text="드라이런은 DB에 반영하지 않고 검증만 수행합니다. 실제 반영하려면 OFF로 바꿔 업로드하세요.">
          <template #activator="{ props }">
            <v-chip
              v-bind="props"
              size="small"
              :color="dryRunState ? 'primary' : 'grey-lighten-2'"
              :text-color="dryRunState ? 'white' : undefined"
              label
              class="font-weight-medium"
              @click="toggleDryRun"
              style="cursor:pointer"
            >
              {{ dryRunState ? '드라이런: ON' : '드라이런: OFF' }}
            </v-chip>
          </template>
        </v-tooltip>
      </div>
    </v-card-title>

    <v-divider class="mb-4" />

    <!-- ───────────── 마감 경고 ───────────── -->
    <v-alert
      v-if="dayClosed"
      type="warning"
      variant="tonal"
      border="start"
      class="mb-4"
    >
      {{ t('board.closedUploadBlocked') }}
    </v-alert>

    <!-- ───────────── (옵션) 파트 선택 (FNB/은행 등) ───────────── -->
    <div v-if="partitionVisible" class="mb-3">
      <label class="label">{{ t('board.partsLabel') }}</label>

      <!-- 칩 선택형 -->
      <v-chip-group
        v-if="Array.isArray(partitionItems) && partitionItems.length"
        v-model="partition"
        column
        class="part-chips"
        :multiple="false"
        selected-class="selected"
      >
        <v-chip
          v-for="p in partitionItems"
          :key="String(p)"
          :value="String(p)"
          label
          filter
          variant="tonal"
          class="part-chip"
        >
          <span class="ellipsis">{{ String(p) }}</span>
        </v-chip>
      </v-chip-group>

      <!-- 텍스트 입력형 -->
      <v-text-field
        v-else
        v-model="partition"
        :label="t('board.partitionPlaceholder')"
        variant="outlined"
        density="comfortable"
        hide-details
        class="mt-2"
      />
    </div>

    <!-- ───────────── 드래그&드롭 영역 ───────────── -->
    <div
      class="dropzone"
      :class="{ 'is-dragover': isDragOver, disabled: disabled }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
    >
      <div class="dz-inner">
        <v-icon icon="mdi-tray-arrow-up" size="28" class="mb-2" />
        <div class="dz-title">{{ dropTitle }}</div>
        <div class="dz-sub">
          {{ acceptHint }}<template v-if="maxSizeMB > 0"> · {{ maxSizeMB }}MB</template>
        </div>
        <div class="row mt-3" style="display:flex;gap:8px;justify-content:center">
          <v-btn variant="tonal" size="small" @click="pickFile" :disabled="disabled">
            {{ t('cta.import') }}
          </v-btn>

          <!-- 템플릿 미리보기 → 다운로드 -->
          <v-menu v-model="templateMenu" :close-on-content-click="false" location="bottom">
            <template #activator="{ props }">
              <v-btn v-bind="props" variant="text" size="small" prepend-icon="mdi-eye-outline">
                템플릿 미리보기
              </v-btn>
            </template>
            <v-card min-width="420">
              <v-card-title class="text-subtitle-2 font-weight-bold">템플릿 미리보기</v-card-title>
              <v-divider />
              <v-card-text>
                <v-alert type="info" variant="tonal" class="mb-2">
                  {{ templateHeaderText || '템플릿 헤더를 불러오는 중...' }}
                </v-alert>
                <div class="text-body-2" style="color:#6b7280">
                  템플릿을 다운로드 후 해당 형식에 맞춰 데이터를 입력해 업로드하세요.
                </div>
              </v-card-text>
              <v-card-actions class="justify-end">
                <v-btn variant="text" @click="templateMenu=false">닫기</v-btn>
                <v-btn color="primary" @click="downloadTemplate" prepend-icon="mdi-download">
                  다운로드
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-menu>
        </div>
      </div>
      <input
        ref="fileEl"
        type="file"
        :accept="acceptAttr"
        :multiple="multiple"
        class="hidden"
        @change="onPicked"
      />
    </div>

    <!-- ───────────── 선택 파일 리스트 ───────────── -->
    <div v-if="files.length" class="mt-3">
      <v-table density="comfortable">
        <thead>
          <tr>
            <th class="text-left">파일명</th>
            <th class="text-right">크기</th>
            <th class="text-right">유형</th>
            <th class="text-right">작업</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(f, i) in files" :key="f.name + ':' + f.size + ':' + i">
            <td class="text-left">{{ f.name }}</td>
            <td class="text-right">{{ fmtSize(f.size) }}</td>
            <td class="text-right">{{ f.type || '-' }}</td>
            <td class="text-right">
              <v-tooltip text="선택한 파일을 목록에서 제거합니다.">
                <template #activator="{ props }">
                  <v-btn v-bind="props" icon="mdi-delete-outline" size="small" variant="text" @click="removeAt(i)" />
                </template>
              </v-tooltip>
            </td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <!-- ───────────── 업로드 버튼 ───────────── -->
    <div class="d-flex justify-end mt-3">
      <v-btn
        color="primary"
        :loading="loading"
        :disabled="disabled || !canUpload"
        prepend-icon="mdi-upload"
        @click="onUpload"
      >
        <template v-if="loading">업로드 중...</template>
        <template v-else>{{ t('board.upload') }}</template>
      </v-btn>
    </div>

    <!-- ───────────── 업로드 결과 요약 ───────────── -->
    <div v-if="summary" class="mt-4">
      <v-alert
        :type="summary.dry_run ? 'info' : 'success'"
        :title="summary.dry_run ? '드라이런 결과' : '업로드 완료'"
        variant="flat"
        border="start"
      >
        <div class="d-flex align-center flex-wrap" style="gap:12px">
          <div class="text-body-2">
            <v-icon v-if="summary.dry_run" icon="mdi-flask-outline" class="mr-1" />
            <v-icon v-else icon="mdi-check-circle-outline" class="mr-1" />
            <span>
              {{ summaryText }}
            </span>
          </div>
          <v-chip v-if="summary.version_no" color="primary" size="small" label>
            v{{ summary.version_no }}
          </v-chip>
        </div>

        <!-- 미리보기(드라이런) 상위 3행 -->
        <div v-if="Array.isArray(summary.preview) && summary.preview.length" class="mt-3">
          <div class="text-caption mb-1" style="color:#6b7280">프리뷰(상위 3행): key_hash / record_hash</div>
          <v-table density="compact">
            <thead>
              <tr>
                <th>key_tuple</th>
                <th>key_hash</th>
                <th>record_hash</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in summary.preview" :key="i">
                <td><code style="word-break:break-all">{{ String(r.key_tuple) }}</code></td>
                <td><code style="word-break:break-all">{{ r.key_hash }}</code></td>
                <td><code style="word-break:break-all">{{ r.record_hash }}</code></td>
              </tr>
            </tbody>
          </v-table>
        </div>
      </v-alert>
    </div>

    <!-- ───────────── 업로드 이력(최신 강조) ───────────── -->
    <div v-if="showHistory && versions.length" class="mt-4">
      <v-card variant="flat" ref="versionsRef">
        <v-card-title class="text-subtitle-2 font-weight-medium d-flex align-center" style="gap:8px">
          <v-icon icon="mdi-history" size="18" /> 업로드 이력
          <v-tooltip text="가장 최근 업로드는 파란 배경으로 강조됩니다.">
            <template #activator="{ props }">
              <v-icon v-bind="props" icon="mdi-information-outline" size="16" />
            </template>
          </v-tooltip>
        </v-card-title>
        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width:90px">Version</th>
              <th>Filename</th>
              <th style="width:120px" class="text-right">Size</th>
              <th style="width:180px">UploadedAt</th>
              <th style="width:120px">Part</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(v, i) in versions"
              :key="v.version_no + ':' + (v.part_key || '') + ':' + i"
              :class="i === 0 ? 'latest-row' : ''"
            >
              <td>v{{ v.version_no }}</td>
              <td>{{ v.filename }}</td>
              <td class="text-right">{{ fmtSize(v.size || 0) }}</td>
              <td>{{ v.uploaded_at }}</td>
              <td>{{ v.part_key || '' }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </div>

  </v-card>
</template>

<script setup lang="ts">
/* ============================================================================
  구현 규칙:
    - axios 금지, '@/services/http'의 fetch 래퍼만 사용
    - props.dryRun을 "초기값"으로 받고 내부 상태(dryRunState)로 제어
    - 업로드 성공 시 emit('done', { response, summary })
============================================================================ */
import { computed, reactive, ref, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

/* ───────────── i18n & toast ───────────── */
const { t } = useI18n()
const { success, error, info } = useToast()

/* ───────────── Props / Emits ───────────── */
const props = defineProps<{
  open?: boolean                 // 과거 호환: 표시에는 영향 없음
  dataset: string
  bizDate: string
  propertyCode: string
  dayStatus?: 'OPEN' | 'CLOSED' | 'LOCKED'
  dryRun?: boolean | null        // 초기값(기본 true로 가정)
  multiple?: boolean
  accept?: string[] | string
  maxSizeMB?: number
  endpoint?: string              // 기본: `/upload/{dataset}`
  partitionItems?: Array<string | number>
  partitionVisible?: boolean
  extraFields?: Record<string, string | number | boolean> | null
  showHistory?: boolean          // 기본 true: 업로드 이력 표시
}>()

const emit = defineEmits<{
  (e: 'done', payload: { response: any; summary?: Summary | null }): void
}>()

/* ───────────── State ───────────── */
type Summary = {
  ok?: boolean
  dry_run?: boolean
  counts?: { rows?: number; inserted?: number; upserted?: number; deleted?: number; noop?: number }
  result?: { inserted?: number; upserted?: number; deleted?: number; noop?: number }
  version_no?: number
  received?: number
  preview?: Array<{ key_tuple: unknown; key_hash: string; record_hash: string }>
  [k: string]: any
}

const loading = ref(false)
const files = reactive<File[]>([])
const fileEl = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const partition = ref<string>('')                 // part 값(선택)
const summary = ref<Summary | null>(null)
const versions = ref<any[]>([])
const versionsRef = ref<HTMLElement | null>(null)

const templateMenu = ref(false)
const templateHeaderText = ref('')

/* 드라이런 내부 상태(초기값: props.dryRun ?? true) */
const dryRunState = ref<boolean>(props.dryRun ?? true)

/* ───────────── Computed ───────────── */
const dayClosed = computed(() => props.dayStatus === 'CLOSED' || props.dayStatus === 'LOCKED')
const maxSizeMB = computed(() => props.maxSizeMB ?? 32)
const multiple = computed(() => props.multiple ?? false)
const acceptAttr = computed(() => {
  const a = props.accept ?? ['.csv', '.xlsx', '.xls']
  return Array.isArray(a) ? a.join(',') : a
})
const endpoint = computed(() => props.endpoint || `/upload/${props.dataset}`)
const disabled = computed(() => loading.value || dayClosed.value)
const partitionVisible = computed(() => !!props.partitionVisible)
const partitionItems = computed(() => props.partitionItems ?? [])
const showHistory = computed(() => props.showHistory !== false)

/* 헤더 타이틀/힌트 */
const headerTitle = computed(() => {
  switch (props.dataset) {
    case 'sales_front':   return '객실 매출 업로드'
    case 'rooms_status':  return '예약/객실 상태 업로드'
    case 'fnb_items':     return 'F&B 상품별 매출 업로드'
    case 'fnb_tenders':   return 'F&B 결제수단별 매출 업로드'
    case 'expenses':      return '지출 내역 업로드'
    case 'bank_ledger':   return '입금/출금 내역 업로드'
    default:              return '데이터 업로드'
  }
})
const headerHint = computed(() => {
  switch (props.dataset) {
    case 'sales_front':   return '스냅샷 방식 — 기존 동일 키 데이터가 교체됩니다.'
    case 'rooms_status':  return 'append 방식 — 일자/객실 기준으로 상태가 누적 기록됩니다.'
    case 'fnb_items':     return '스냅샷 방식 — 품목별 금액/건수를 반영합니다.'
    case 'fnb_tenders':   return '스냅샷 방식 — 결제수단별 금액/건수를 반영합니다.'
    case 'expenses':      return '스냅샷 방식 — 계정코드별 금액을 반영합니다.'
    case 'bank_ledger':   return 'append 방식 — 입금/출금 라인이 누적되며 누락은 무시됩니다.'
    default:              return '표준 SSOT 병합 엔진 정책이 적용됩니다.'
  }
})

/* 드롭존 UI 텍스트 */
const dropTitle = computed(() =>
  multiple.value ? '파일을 드래그 앤 드롭하거나 버튼으로 선택하세요'
                 : '파일을 여기에 드래그 앤 드롭하세요'
)
const acceptHint = computed(() => Array.isArray(props.accept) ? props.accept.join(', ') : (props.accept || '.csv,.xlsx,.xls'))

/* 업로드 가능 여부 */
const canUpload = computed(() => {
  if (!files.length) return false
  if (partitionVisible.value && partitionItems.value.length > 1 && !partition.value) return false
  return true
})

/* 업로드 결과 설명 텍스트(드라이런/실업로드 모두 커버) */
const summaryText = computed(() => {
  const s = summary.value
  if (!s) return ''
  const rows = s?.counts?.rows ?? s?.received ?? files.length
  if (s.dry_run) return `데이터 검증이 완료되었습니다. 행 수: ${rows}건`
  const ins = s.result?.inserted ?? s.counts?.inserted ?? 0
  const upd = s.result?.upserted ?? s.counts?.upserted ?? 0
  const del = s.result?.deleted ?? s.counts?.deleted ?? 0
  const np  = s.result?.noop     ?? s.counts?.noop     ?? 0
  return `반영 결과 — insert: ${ins}, upsert: ${upd}, delete: ${del}, noop: ${np}`
})

/* ───────────── Helpers ───────────── */
function toggleDryRun() {
  dryRunState.value = !dryRunState.value
}

function pickFile() { fileEl.value?.click() }

function onPicked(ev: Event) {
  const el = ev.target as HTMLInputElement
  const list = el.files
  if (!list || !list.length) return
  pushFiles(list)
  el.value = ''
}

function onDragOver() { if (!disabled.value) isDragOver.value = true }
function onDragLeave() { isDragOver.value = false }

function onDrop(ev: DragEvent) {
  isDragOver.value = false
  if (disabled.value) return
  const list = ev.dataTransfer?.files
  if (!list || !list.length) return
  pushFiles(list)
}

function pushFiles(list: FileList) {
  const max = maxSizeMB.value * 1024 * 1024
  const next: File[] = []
  for (let i = 0; i < list.length; i++) {
    const f = list[i]
    if (max > 0 && f.size > max) { error(t('msg.fileTooLarge')); continue }
    if (!isAccepted(f)) { error(t('msg.fileType')); continue }
    next.push(f)
  }
  if (!next.length) return
  if (multiple.value) files.push(...next)
  else files.splice(0, files.length, next[0])
}

function isAccepted(file: File) {
  const a = acceptAttr.value
  if (!a) return true
  const parts = a.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
  if (!parts.length) return true
  const name = file.name.toLowerCase()
  const type = (file.type || '').toLowerCase()
  return parts.some(p => (p.startsWith('.') ? name.endsWith(p) : type.includes(p)))
}

function removeAt(i: number) { files.splice(i, 1) }

function fmtSize(n: number) {
  if (!n) return '0B'
  if (n < 1024) return `${n}B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)}KB`
  return `${(n / (1024 * 1024)).toFixed(1)}MB`
}

/* ───────────── 템플릿: 미리보기 & 다운로드 ───────────── */
watch(templateMenu, async (open) => {
  if (!open) return
  try {
    // 템플릿 헤더만 간단 추출 (백엔드가 CSV 헤더 한 줄을 반환)
    const url = `/templates/${encodeURIComponent(props.dataset)}.csv`
    // http.get은 JSON 가정이므로 텍스트는 window.fetch 직접 사용
    const res = await fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
    const text = await res.text()
    templateHeaderText.value = (text || '').split('\n')[0] || ''
  } catch {
    templateHeaderText.value = '헤더 로드 실패'
  }
})

function downloadTemplate() {
  const url = `/api/templates/${encodeURIComponent(props.dataset)}.csv`
  // 간단/안정: 새 탭 열기 (프록시/권한 헤더는 서버 설정에 따름)
  window.open(url, '_blank')
}

/* ───────────── 업로드 ───────────── */
async function onUpload() {
  if (dayClosed.value) { error(t('board.closedUploadBlocked')); return }
  if (!files.length) { error(t('msg.fileRequired')); return }
  if (partitionVisible.value && partitionItems.value.length > 1 && !partition.value) {
    error(t('board.partitionRequired')); return
  }

  const fd = new FormData()
  fd.append('property_code', props.propertyCode)
  fd.append('business_date', props.bizDate)
  fd.append('dry_run', dryRunState.value ? '1' : '0')
  if (partitionVisible.value && partition.value) fd.append('part', partition.value) // 무시돼도 안전
  if (props.extraFields) Object.entries(props.extraFields).forEach(([k, v]) => fd.append(k, String(v)))
  files.forEach((f, i) => fd.append(multiple.value ? `file_${i + 1}` : 'file', f))

  try {
    loading.value = true
    summary.value = null

    const res: any = await http.post(endpoint.value, fd) // fetch 래퍼(JSON 응답 가정)
    // 표준화된 summary 구성 (dry-run/실업로드 모두 커버)
    summary.value = {
      dry_run: !!res?.dry_run,
      counts: res?.counts || res?.result || {},
      result: res?.result,
      version_no: res?.version_no,
      received: res?.received,
      preview: res?.preview,
      ...res,
    }

    if (res?.dry_run) {
      info(`드라이런 완료 — ${summary.value.counts?.rows ?? summary.value.received ?? files.length}건`)
    } else {
      success(`업로드 완료 (${props.dataset})`)
      emit('done', { response: res, summary: summary.value })
      files.splice(0)
    }

    await loadVersions()
    // 최신 이력이 보이도록 스크롤
    await nextTick()
    versionsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })

  } catch (e: any) {
    // http.ts가 throw하는 에러 객체 형식에 맞춰 메시지 출력
    error(e?.message || '업로드 중 오류가 발생했습니다.')
    console.warn('upload error:', e)
  } finally {
    loading.value = false
  }
}

/* ───────────── 이력 로드 ───────────── */
async function loadVersions() {
  if (!showHistory.value) return
  try {
    const url =
      `/upload/versions?dataset=${encodeURIComponent(props.dataset)}` +
      `&property_code=${encodeURIComponent(props.propertyCode)}` +
      `&business_date=${encodeURIComponent(props.bizDate)}`
    const res: any = await http.get(url)
    versions.value = Array.isArray(res?.items) ? res.items : []
  } catch {
    versions.value = []
  }
}

/* 초기 로드: 이력 불러오기 */
onMounted(() => { loadVersions() })
</script>

<style scoped>
/* 카드/영역 */
.upload-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; }
.dropzone {
  position: relative;
  border: 2px dashed var(--color-line, #e5e7eb);
  border-radius: 12px;
  background: linear-gradient(180deg, #fafbff, #f7f8fb);
  min-height: 140px;
  display: grid;
  place-items: center;
  transition: .15s;
}
.dropzone.is-dragover { border-color: var(--brand-secondary, #3ba6a1); box-shadow: 0 0 0 4px rgba(58,166,161,.12); }
.dropzone.disabled { opacity: .6; pointer-events: none; }
.dz-inner { text-align: center; padding: 18px; }
.dz-title { font-weight: 600; color: #374151; }
.dz-sub { font-size: .9rem; color: #6b7280; margin-top: 2px; }

.label { font-weight: 600; color: #6b7280; }
.part-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.part-chip { max-width: 220px; }
.ellipsis { display: inline-block; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.hidden { display: none; }

/* 이력 최신행 강조 */
.latest-row { background-color: rgba(33, 150, 243, 0.08); font-weight: 600; }
</style>

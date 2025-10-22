<!-- ============================================================================
  File    : src/ui/components/closing/DialogUpload.vue
  Version : 1.7.0 (2025-10-22 Final Stable · Property AutoSync)
  Purpose : Hotel Admin — 공통 업로드 다이얼로그 (CSV / 문서 업로드)
  ------------------------------------------------------------------------------
  목적:
    • 데이터셋별 업로드(직원, OTA, 매출 등) 공통 다이얼로그
    • v-model:open 으로 제어
    • 템플릿 다운로드 + 파일 업로드 + property_code 자동 포함
  ------------------------------------------------------------------------------
  개선사항 (v1.7.0)
    ✅ property_code 자동 주입 (localStorage → .env → MOP)
    ✅ http.headers() 일관 적용 (X-Internal-Token 포함)
    ✅ FormData 처리 시 Content-Type 자동 관리
    ✅ fetch → http.url() 기반 호출 정리
============================================================================ -->

<template>
  <v-dialog
    :model-value="open"
    max-width="560"
    persistent
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-2xl">
      <!-- ───── 헤더 ───── -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-tray-arrow-up" size="20" class="text-primary" />
          <span class="text-h6 font-weight-medium">{{ title || '데이터 업로드' }}</span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <!-- ───── 본문 ───── -->
      <v-card-text class="px-5 py-4">
        <div class="text-body-2 text-medium-emphasis mb-3">
          데이터셋: <b>{{ dataset }}</b>
          <span v-if="bizDate"> · 기준일: <b>{{ bizDate }}</b></span>
          <span v-if="finalProperty"> · 사업장: <b>{{ finalProperty }}</b></span>
        </div>

        <!-- 드래그 & 드롭 -->
        <div
          class="drop-zone mb-3"
          @dragover.prevent
          @dragenter.prevent="dragOver = true"
          @dragleave.prevent="dragOver = false"
          @drop.prevent="onDrop"
          :class="{ 'is-over': dragOver }"
        >
          <div class="inner">
            <v-icon size="28" class="mr-2">mdi-file-upload-outline</v-icon>
            <div class="text">
              <div class="title">여기로 파일을 끌어다 놓으세요</div>
              <div class="caption">또는 아래 버튼으로 파일 선택</div>
            </div>
          </div>
        </div>

        <!-- 파일 선택 -->
        <div class="d-flex align-center gap-2">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-folder-open"
            @click="pickFile"
            :disabled="uploading"
          >
            파일 선택
          </v-btn>
          <div class="text-caption text-medium-emphasis">허용: CSV (권장), XLSX</div>
        </div>

        <!-- 선택된 파일 -->
        <div v-if="file" class="mt-3 d-flex align-center gap-2">
          <v-icon size="18">mdi-file-check-outline</v-icon>
          <span class="text-body-2">{{ file.name }}</span>
          <v-spacer />
          <v-btn size="small" variant="text" color="grey" @click="clearFile" :disabled="uploading">지우기</v-btn>
        </div>

        <!-- 템플릿 다운로드 -->
        <div class="mt-4">
          <v-btn
            variant="tonal"
            color="primary"
            prepend-icon="mdi-download"
            @click="downloadTemplate"
            :loading="downloading"
            :disabled="downloading || !dataset"
          >
            템플릿 다운로드 ({{ dataset }}.csv)
          </v-btn>
        </div>
      </v-card-text>

      <v-divider />

      <!-- ───── 푸터 ───── -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" color="grey" @click="emit('update:open', false)">닫기</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-tray-arrow-up"
          :loading="uploading"
          :disabled="!canUpload"
          @click="onUpload"
        >
          업로드
        </v-btn>
      </v-card-actions>

      <!-- 숨은 파일 입력 -->
      <input
        ref="fileInput"
        type="file"
        accept=".csv, .xlsx"
        class="hidden-input"
        @change="onFileChange"
      />
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ===========================================================================
   공통 업로드 다이얼로그 — Dataset / Property / BizDate 자동 전송
   ---------------------------------------------------------------------------
   주요 흐름:
     1. dataset, bizDate, property_code 상위 전달
     2. property_code 자동 보정 (localStorage → env → MOP)
     3. fetch(http.url(`upload/${dataset}`)) POST FormData
=========================================================================== */
import { ref, computed } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import http from '@/services/http'

/* Props / Emits */
const props = defineProps<{
  open: boolean
  title?: string
  dataset: string
  bizDate?: string | null
  propertyCode?: string | null
  autoRefresh?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'uploaded', payload: any): void
}>()

/* 상태 */
const { success, error } = useToast()
const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const downloading = ref(false)
const dragOver = ref(false)
const canUpload = computed(() => !!file.value && !!props.dataset)

/* ✅ property_code 자동 보정 */
const finalProperty = computed(() =>
  props.propertyCode ||
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'
)

/* 파일 제어 */
function pickFile() { fileInput.value?.click() }
function clearFile() { file.value = null }
function onFileChange(e: Event) {
  const t = e.target as HTMLInputElement
  const f = t.files?.[0]
  if (f) file.value = f
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) file.value = f
}

/* 템플릿 다운로드 */
async function downloadTemplate() {
  if (!props.dataset) return
  try {
    downloading.value = true
    const blob = await http.getBlob(`templates/${props.dataset}.csv`)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.dataset}.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    success('템플릿을 내려받았습니다.')
  } catch (e: any) {
    error('템플릿 다운로드 실패: ' + (e?.message || '서버 오류'))
  } finally {
    downloading.value = false
  }
}

/* 업로드 */
async function onUpload() {
  if (!file.value || !props.dataset) {
    error('파일과 데이터셋을 확인하세요.')
    return
  }
  try {
    uploading.value = true

    const fd = new FormData()
    fd.append('file', file.value)
    if (props.bizDate) fd.append('business_date', props.bizDate)
    if (finalProperty.value) fd.append('property_code', finalProperty.value)

    // ✅ 최신 엔드포인트: /api/upload/{dataset}
    const res = await fetch(http.url(`upload/${props.dataset}`), {
      method: 'POST',
      headers: http.headers(), // X-Internal-Token 포함
      body: fd,
    })

    if (!res.ok) {
      const msg = await res.text().catch(() => '')
      throw new Error(msg || `HTTP ${res.status}`)
    }

    const payload = await res.json().catch(() => ({}))
    success('업로드가 완료되었습니다.')
    emit('uploaded', payload)

    if (props.autoRefresh) {
      // 상위 컴포넌트에서 uploaded 이벤트 수신 후 새로고침
    }

    clearFile()
    emit('update:open', false)
  } catch (e: any) {
    error('업로드 실패: ' + (e?.message || '서버 오류'))
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.hidden-input { display: none; }
.drop-zone {
  border: 1px dashed var(--color-line, #D0D5DD);
  border-radius: 10px;
  background: rgb(248, 250, 252);
  padding: 22px 18px;
  transition: background .15s ease, border-color .15s ease;
}
.drop-zone.is-over {
  background: #eef6ff;
  border-color: #84c5ff;
}
.drop-zone .inner { display: flex; align-items: center; }
.drop-zone .inner .text .title { font-weight: 600; }
.drop-zone .inner .text .caption { font-size: .85rem; color: #6b7280; }
</style>

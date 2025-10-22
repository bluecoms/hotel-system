<template>
  <v-dialog
    :model-value="open"
    max-width="720"
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-upload" class="mr-1" />
          {{ titleText }}
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-alert
          v-if="dayClosed"
          type="warning"
          variant="tonal"
          class="mb-4"
        >
          {{ t('board.closedUploadBlocked') }}
        </v-alert>

        <div class="meta row mb-3">
          <v-chip size="small" variant="outlined">{{ t('closing.property') }}: {{ propertyCode }}</v-chip>
          <v-chip size="small" variant="tonal">{{ bizDate }}</v-chip>
          <v-chip
            v-if="dryRun !== null"
            :color="dryRun ? 'primary' : 'grey-lighten-2'"
            :text-color="dryRun ? 'white' : undefined"
            size="small"
            label
          >
            {{ dryRun ? '드라이런: ON' : '드라이런: OFF' }}
          </v-chip>
        </div>

        <div v-if="partitionVisible" class="mb-3">
          <label class="label">{{ t('board.partsLabel') }}</label>
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
              {{ acceptHint }}
              <template v-if="maxSizeMB > 0"> · {{ maxSizeMB }}MB</template>
            </div>
            <div class="row mt-3">
              <v-btn variant="tonal" size="small" @click="pickFile" :disabled="disabled">
                {{ t('cta.import') }}
              </v-btn>
              <v-btn variant="text" size="small" prepend-icon="mdi-download" :href="templateHref" target="_blank" rel="noopener">
                {{ t('board.template') }}
              </v-btn>
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

        <div v-if="files.length" class="mt-3">
          <v-table density="comfortable">
            <thead>
              <tr>
                <th class="text-left">Filename</th>
                <th class="text-right">Size</th>
                <th class="text-right">Type</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(f, i) in files" :key="f.name + ':' + f.size + ':' + i">
                <td class="text-left">{{ f.name }}</td>
                <td class="text-right">{{ fmtSize(f.size) }}</td>
                <td class="text-right">{{ f.type || '-' }}</td>
                <td class="text-right">
                  <v-btn icon="mdi-delete-outline" size="small" variant="text" @click="removeAt(i)" />
                </td>
              </tr>
            </tbody>
          </v-table>
        </div>

        <div v-if="summary" class="mt-4">
          <v-alert type="info" variant="tonal" border="start">
            <div class="d-flex flex-column gap-1">
              <div><b>rows:</b> {{ summary.counts?.rows ?? 0 }}</div>
              <div v-if="summary.counts?.insert"><b>insert:</b> {{ summary.counts.insert }}</div>
              <div v-if="summary.counts?.update"><b>update:</b> {{ summary.counts.update }}</div>
              <div v-if="summary.counts?.noop"><b>noop:</b> {{ summary.counts.noop }}</div>
              <div v-if="summary.version_no"><b>version:</b> v{{ summary.version_no }}</div>
            </div>
          </v-alert>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="emit('update:open', false)">{{ t('cta.close') }}</v-btn>
        <v-btn
          color="primary"
          :loading="loading"
          :disabled="disabled || !canUpload"
          prepend-icon="mdi-upload"
          @click="onUpload"
        >
          {{ t('board.upload') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

type Summary = {
  dry_run?: boolean
  counts?: { rows?: number; insert?: number; update?: number; noop?: number }
  version_no?: number
  received?: number
  [k: string]: any
}

const props = defineProps<{
  open: boolean
  dataset: string
  bizDate: string
  propertyCode: string
  dayStatus?: 'OPEN' | 'CLOSED'
  dryRun?: boolean | null
  multiple?: boolean
  accept?: string[] | string
  maxSizeMB?: number
  endpoint?: string
  partitionItems?: Array<string | number>
  partitionVisible?: boolean
  extraFields?: Record<string, string | number | boolean> | null
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'done', payload: { response: any; summary?: Summary }): void
}>()

const { t } = useI18n()
const { success, error, info } = useToast()

const loading = ref(false)
const files = reactive<File[]>([])
const fileEl = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const partition = ref<string>('')

const dayClosed = computed(() => props.dayStatus === 'CLOSED')
const maxSizeMB = computed(() => props.maxSizeMB ?? 32)
const multiple = computed(() => props.multiple ?? false)
const acceptAttr = computed(() => {
  const a = props.accept ?? ['.csv', '.xlsx']
  return Array.isArray(a) ? a.join(',') : a
})
const titleText = computed(() => t('board.upload'))
const acceptHint = computed(() => (Array.isArray(props.accept) ? props.accept.join(', ') : (props.accept || '.csv,.xlsx')))
const templateHref = computed(() => http.url(`templates/${props.dataset}.csv`))
const endpoint = computed(() => props.endpoint || `/upload/${props.dataset}`)
const disabled = computed(() => loading.value || dayClosed.value)
const partitionVisible = computed(() => !!props.partitionVisible)
const partitionItems = computed(() => props.partitionItems ?? [])

const dropTitle = computed(() => {
  if (multiple.value) return '파일을 여기에 드래그 앤 드롭하거나 버튼으로 선택'
  return '파일을 여기에 드래그 앤 드롭하세요'
})

const canUpload = computed(() => {
  if (!files.length) return false
  if (partitionVisible.value && partitionItems.value.length > 1 && !partition.value) return false
  return true
})

const summary = ref<Summary | null>(null)

function pickFile() {
  fileEl.value?.click()
}

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
    if (max > 0 && f.size > max) {
      error(t('msg.fileTooLarge'))
      continue
    }
    if (!isAccepted(f)) {
      error(t('msg.fileType'))
      continue
    }
    next.push(f)
  }
  if (!next.length) return
  if (multiple.value) {
    files.push(...next)
  } else {
    files.splice(0, files.length, next[0])
  }
}

function isAccepted(file: File) {
  const a = acceptAttr.value
  if (!a) return true
  const parts = a.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
  if (!parts.length) return true
  const name = file.name.toLowerCase()
  const type = (file.type || '').toLowerCase()
  return parts.some(p => {
    if (p.startsWith('.')) return name.endsWith(p)
    // mime support (rough)
    return type.includes(p)
  })
}

function removeAt(i: number) { files.splice(i, 1) }

function fmtSize(n: number) {
  if (!n) return '0B'
  if (n < 1024) return `${n}B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)}KB`
  return `${(n / (1024 * 1024)).toFixed(1)}MB`
}

async function onUpload() {
  if (dayClosed.value) { error(t('board.closedUploadBlocked')); return }
  if (!files.length) { error(t('msg.fileRequired')); return }
  if (partitionVisible.value && partitionItems.value.length > 1 && !partition.value) {
    error(t('board.partitionRequired')); return
  }

  const fd = new FormData()
  fd.append('property_code', props.propertyCode)
  fd.append('business_date', props.bizDate)
  if (props.dryRun !== null && props.dryRun !== undefined) {
    fd.append('dry_run', props.dryRun ? '1' : '0')
  }
  if (partitionVisible.value && partition.value) {
    fd.append('part', partition.value)
  }
  if (props.extraFields) {
    Object.entries(props.extraFields).forEach(([k, v]) => fd.append(k, String(v)))
  }

  files.forEach((f, i) => {
    const key = multiple.value ? `file_${i + 1}` : 'file'
    fd.append(key, f)
  })

  try {
    loading.value = true
    summary.value = null
    const res: any = await http.post(endpoint.value, fd)
    summary.value = {
      dry_run: !!res?.dry_run,
      counts: res?.counts,
      version_no: res?.version_no,
      received: res?.received,
      ...res,
    }
    if (res?.dry_run) {
      info(`드라이런: ${res?.counts?.rows ?? res?.received ?? files.length}건`)
    } else {
      success(`업로드 완료 (${props.dataset})`)
      emit('done', { response: res, summary: summary.value || undefined })
      emit('update:open', false)
    }
  } catch (e: any) {
    error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.label {
  font-weight: 600;
  color: var(--color-muted);
}

.part-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.part-chip { max-width: 220px; }
.ellipsis {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropzone {
  position: relative;
  border: 2px dashed var(--color-line);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, #fafbff, #f7f8fb);
  min-height: 140px;
  display: grid;
  place-items: center;
  transition: border-color .15s ease, background-color .15s ease, box-shadow .15s ease;
}
.dropzone.is-dragover {
  border-color: var(--brand-secondary);
  box-shadow: 0 0 0 4px rgba(58, 166, 161, .12);
}
.dropzone.disabled {
  opacity: .6;
  pointer-events: none;
}
.dz-inner { text-align: center; padding: 18px; }
.dz-title { font-weight: 600; color: #374151; }
.dz-sub { font-size: .9rem; color: var(--color-muted); margin-top: 2px; }

.hidden { display: none; }

.meta .v-chip { margin-right: 6px; }
</style>

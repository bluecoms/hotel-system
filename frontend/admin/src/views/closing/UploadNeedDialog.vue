<template>
  <v-dialog
    v-model="localModel"
    max-width="520"
    :retain-focus="false"
    scrollable
  >
    <v-card class="brand-panel">
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="d-flex flex-column">
          <span class="text-subtitle-1 font-weight-bold">업로드 필요 항목</span>
          <span class="text-caption text-medium-emphasis" v-if="subtitle">
            {{ subtitle }}
          </span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="close" aria-label="닫기"></v-btn>
      </v-card-title>

      <v-card-text class="pt-0">
        <div class="d-flex align-center mb-2" style="gap: 8px">
          <v-chip size="x-small" color="orange" variant="tonal">필수 파트 부족</v-chip>
          <v-chip size="x-small" color="primary" variant="tonal">항목 이동 가능</v-chip>
          <v-chip size="x-small" color="grey" variant="tonal">템플릿 안내 포함</v-chip>
        </div>

        <v-list density="comfortable" nav class="rounded">
          <template v-for="it in normalizedItems" :key="it.key">
            <v-list-item
              :value="it.key"
              class="cursor-pointer"
              @click="goto(it)"
              role="button"
              tabindex="0"
            >
              <template #prepend>
                <v-avatar size="28"><v-icon :icon="it.icon" :color="it.color" /></v-avatar>
              </template>

              <v-list-item-title class="d-flex align-center" style="gap:8px">
                <span class="text-body-2">{{ it.label }}</span>
                <v-chip
                  v-if="it.requiredCount > 0"
                  size="x-small"
                  :color="it.missingCount > 0 ? 'orange' : 'green'"
                  :variant="it.missingCount > 0 ? 'tonal' : 'flat'"
                  label
                >
                  Parts {{ it.requiredCount - it.missingCount }}/{{ it.requiredCount }}
                </v-chip>
              </v-list-item-title>

              <v-list-item-subtitle v-if="it.desc" class="text-caption">
                {{ it.desc }}
              </v-list-item-subtitle>

              <template #append>
                <div class="d-flex align-center" style="gap:6px">
                  <v-tooltip location="top" v-if="it.template">
                    <template #activator="{ props }">
                      <v-btn v-bind="props" size="small" variant="text" icon="mdi-file-document-outline" />
                    </template>
                    <div class="mono">{{ it.template }}</div>
                  </v-tooltip>
                  <v-btn size="small" color="primary" variant="tonal" @click.stop="goto(it)">
                    이동
                  </v-btn>
                </div>
              </template>
            </v-list-item>

            <div
              v-if="it.missing?.length"
              class="d-flex flex-wrap px-6 pb-2"
              style="gap:6px"
            >
              <v-chip
                v-for="p in it.missing"
                :key="p"
                size="x-small"
                color="orange"
                variant="tonal"
                label
              >{{ p }}</v-chip>
            </div>

            <v-divider></v-divider>
          </template>

          <v-list-item v-if="!normalizedItems.length">
            <template #prepend>
              <v-avatar size="28"><v-icon color="green" icon="mdi-check-circle-outline" /></v-avatar>
            </template>
            <v-list-item-title class="text-medium-emphasis">
              모든 항목 업로드 완료
            </v-list-item-title>
            <template #append>
              <v-btn color="primary" variant="tonal" @click="$emit('goto', 'top')">보드로 이동</v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useToast } from '@/ui/composables/useToast'

const { success } = useToast()

type ItemShape = {
  key: string
  label?: string
  desc?: string
  requiredParts?: string[]
  missingParts?: string[]
  template?: string
}

const props = defineProps<{
  modelValue: boolean
  items: Array<string | ItemShape>
  businessDate?: string
  propertyCode?: string
  headersMap?: Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'goto', anchor: string): void
}>()

const localModel = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

function close() {
  emit('update:modelValue', false)
}

/** 아이콘/색상 */
const iconMap: Record<string, { icon: string; color: string }> = {
  sales_front: { icon: 'mdi-cash-register', color: 'primary' },
  rooms_status: { icon: 'mdi-bed-outline', color: 'primary' },
  fnb_sales: { icon: 'mdi-silverware-fork-knife', color: 'primary' },
  expenses: { icon: 'mdi-receipt-text-outline', color: 'primary' },
  pay_settlement: { icon: 'mdi-credit-card-outline', color: 'primary' },
  default: { icon: 'mdi-file-upload-outline', color: 'primary' },
}

/** 기본 라벨 */
const labelFallback: Record<string, string> = {
  sales_front: 'Front 매출',
  rooms_status: '객실 현황',
  fnb_sales: 'F&B 매출',
  expenses: '지출 내역',
  pay_settlement: '입금 내역',
}

const subtitle = computed(() => {
  const parts = []
  if (props.businessDate) parts.push(`Date: ${props.businessDate}`)
  if (props.propertyCode) parts.push(`Property: ${props.propertyCode}`)
  return parts.join(' • ')
})

/** 문자열/객체 혼합 입력 정규화 */
const normalizedItems = computed(() => {
  const arr = Array.isArray(props.items) ? props.items : []
  return arr.map((raw) => {
    const it = (typeof raw === 'string' ? ({ key: raw } as ItemShape) : raw) as ItemShape
    const key = String(it.key || '').trim()
    const label = it.label || labelFallback[key] || key
    const required = it.requiredParts || []
    const missing = it.missingParts || []
    const template = it.template || props.headersMap?.[key] || ''
    const iconCfg = iconMap[key] || iconMap.default
    return {
      key,
      label,
      desc: it.desc || '',
      requiredCount: required.length,
      missingCount: missing.length,
      missing,
      template,
      icon: iconCfg.icon,
      color: iconCfg.color,
    }
  })
})

function goto(it: { key: string }) {
  success(`${it.key} 업로드 화면으로 이동합니다.`)
  emit('goto', it.key)
}
</script>

<style scoped>
.cursor-pointer { cursor: pointer; }
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  white-space: nowrap;
}
.brand-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}
</style>

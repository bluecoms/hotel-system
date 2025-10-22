<template>
  <div class="contract-tab">
    <div class="brand-subbar d-flex align-center justify-space-between mb-4">
      <div class="d-flex align-center gap8">
        <v-icon icon="mdi-file-document-outline" color="primary" />
        <h3 class="text-h6 font-weight-bold mb-0">근로계약 관리</h3>
      </div>

      <v-btn
        color="primary"
        variant="elevated"
        prepend-icon="mdi-file-document-edit-outline"
        class="btn-action"
        @click="newContract"
      >
        새 계약 등록
      </v-btn>
    </div>

    <v-data-table
      :headers="headers"
      :items="rows"
      :loading="loading"
      density="comfortable"
      class="rounded-xl elevation-1"
      hover
    >
      <template #item.period="{ item }">
        <span class="text-body-2">
          {{ item.start_date }} ~ {{ item.end_date || '미정' }}
        </span>
      </template>

      <template #item.salary="{ item }">
        <span class="font-weight-medium">
          ₩{{ (item.salary_monthly || item.hourly_wage || 0).toLocaleString() }}
        </span>
      </template>

      <template #item.status="{ item }">
        <v-chip
          size="small"
          :color="item.status === 'ACTIVE' ? 'green' : 'grey-lighten-1'"
          :text-color="item.status === 'ACTIVE' ? 'white' : 'grey-darken-1'"
          label
        >
          {{ item.status === 'ACTIVE' ? '유효' : '만료' }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-btn
          size="small"
          variant="text"
          color="primary"
          prepend-icon="mdi-pencil-outline"
          @click="edit(item)"
        >
          수정
        </v-btn>
      </template>

      <template #no-data>
        <div class="py-6 text-center text-grey-darken-1">
          등록된 계약이 없습니다.
        </div>
      </template>
    </v-data-table>

    <DialogContractForm
      v-model:open="openDialog"
      :property-code="'MOP'"
      :biz-date="today"
      :initial="selected"
      @saved="load"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import DialogContractForm from '@/ui/components/DialogContractForm.vue'

const props = defineProps<{ userId: number }>()
const today = new Date().toISOString().slice(0, 10)

const headers = [
  { title: '계약기간', key: 'period', sortable: false },
  { title: '직책', key: 'position' },
  { title: '유형', key: 'contract_type' },
  { title: '급여', key: 'salary', align: 'end' },
  { title: '상태', key: 'status', align: 'center' },
  { title: '', key: 'actions', align: 'center', sortable: false },
]

const rows = ref<any[]>([])
const loading = ref(false)
const openDialog = ref(false)
const selected = ref<any>(null)

async function load() {
  loading.value = true
  try {
    const r = await http.get(`/contracts?user_id=${props.userId}`) as any
    rows.value = Array.isArray(r) ? r : r.items ?? []
  } finally {
    loading.value = false
  }
}

function newContract() {
  selected.value = null
  openDialog.value = true
}

function edit(item: any) {
  selected.value = item
  openDialog.value = true
}

onMounted(load)
</script>

<style scoped>
.contract-tab {
  padding: 8px;
}
.brand-subbar {
  border: 1px solid #e5e7eb;
  background: #fff;
  border-radius: 12px;
  padding: 12px 20px;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08);
}
.btn-action {
  height: 40px;
  font-weight: 600;
}
</style>

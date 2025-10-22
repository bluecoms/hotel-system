  <div class="d-flex align-center" style="gap:8px">
    <v-combobox
      v-model="selectedAcct"
      :items="accountItems"
      label="Account"
      density="comfortable"
      clearable
      hide-details
      style="max-width:240px"
    />
    <v-text-field
      v-model="bizDate"
      label="Date (YYYY-MM-DD)"
      density="comfortable"
      hide-details
      style="max-width:180px"
    />
    <v-btn color="primary" :loading="loading" @click="load">조회</v-btn>
  </div>
</v-card-title>

<v-divider />

<v-card-text>
  <v-alert
    v-if="errorText"
    type="error"
    variant="tonal"
    border="start"
    class="mb-3"
  >{{ errorText }}</v-alert>

  <div class="d-flex flex-wrap mb-3" style="gap:10px">
    <v-chip color="success" label>
      입금 {{ fmtNum(kpis.in_amount) }}
    </v-chip>
    <v-chip color="error" label>
      출금 {{ fmtNum(kpis.out_amount) }}
    </v-chip>
    <v-chip color="primary" label>
      순이동 {{ fmtNum(kpis.net_amount) }}
    </v-chip>
    <v-chip color="grey" label v-if="kpis.last_balance !== null">
      마감잔액 {{ fmtNum(kpis.last_balance || 0) }}
    </v-chip>
  </div>

  <v-skeleton-loader
    v-if="loading"
    type="table"
    class="mt-2"
  />

  <template v-else>
    <v-table density="comfortable" class="mt-2">
      <thead>
        <tr>
          <th style="width:110px">시간</th>
          <th>적요</th>
          <th style="width:120px" class="text-right">입금</th>
          <th style="width:120px" class="text-right">출금</th>
          <th style="width:120px">지점</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in rows" :key="i">
          <td>{{ r.txn_time || '-' }}</td>
          <td>{{ r.note || '-' }}</td>
          <td class="text-right">{{ r.direction==='IN' ? fmtNum(r.amount) : '' }}</td>
          <td class="text-right">{{ r.direction==='OUT' ? fmtNum(r.amount) : '' }}</td>
          <td>{{ r.branch || '-' }}</td>
        </tr>
        <tr v-if="!rows.length">
          <td colspan="5" class="text-center text-medium-emphasis py-6">데이터 없음</td>
        </tr>
      </tbody>
    </v-table>
    <div class="text-caption text-medium-emphasis mt-2">
      최대 20건까지만 미리보기로 표시됩니다.
    </div>
  </template>
</v-card-text>

</v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getBankLedgerSummary, type BankLedgerSummaryResp } from '@/services/reports'

type Row = NonNullable<BankLedgerSummaryResp['items']>[number]

const props = defineProps<{
  propertyCode: string
  defaultAccount?: string
  defaultDate: string
  accounts?: string[]
}>()

const accountItems = computed(() =>
  props.accounts?.length ? props.accounts : ['NH-301-xxxx', 'NH-302-yyyy']
)

const selectedAcct = ref(props.defaultAccount || accountItems.value[0])
const bizDate = ref(props.defaultDate)
const loading = ref(false)
const errorText = ref('')
const versionNo = ref<number | undefined>(undefined)
const rows = ref<Row[]>([])
const kpis = ref({ in_amount: 0, out_amount: 0, net_amount: 0, last_balance: 0 as number | null })

function fmtNum(v?: string | number | null) {
  const n = typeof v === 'string' ? Number(v) : (v ?? 0)
  return Number.isFinite(n) ? n.toLocaleString() : '0'
}

async function load() {
  if (!selectedAcct.value) return
  loading.value = true
  errorText.value = ''
  try {
    const r = await getBankLedgerSummary({
      date: bizDate.value,
      property_code: props.propertyCode,
      account_code: selectedAcct.value,
    })
    versionNo.value = r.version_no
    rows.value = Array.isArray(r.items) ? r.items : []
    kpis.value = {
      in_amount: r.in_amount || 0,
      out_amount: r.out_amount || 0,
      net_amount: r.net_amount || 0,
      last_balance: r.last_balance ?? 0,
    }
  } catch (e: any) {
    errorText.value = e?.message || '조회 실패'
    rows.value = []
    kpis.value = { in_amount: 0, out_amount: 0, net_amount: 0, last_balance: 0 }
  } finally {
    loading.value = false
  }
}

watch(() => [props.propertyCode, bizDate.value, selectedAcct.value], () => load(), { deep: true })
onMounted(load)
</script>

<style scoped>
.gap8 {
  gap: 8px;
}
</style>
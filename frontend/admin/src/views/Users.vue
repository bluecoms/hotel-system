<template>
  <v-container class="py-6">
    <h2 class="text-h5 mb-4">Users</h2>

    <div class="d-flex flex-wrap align-center" style="gap:12px">
      <v-text-field
        v-model="q"
        label="Search (name/email)"
        density="comfortable"
        hide-details
        clearable
        style="max-width:320px"
        @keyup.enter="load(1)"
      />
      <v-btn color="primary" @click="load(1)">Search</v-btn>
      <v-spacer />
      <v-btn color="primary" variant="elevated" @click="openCreate">New User</v-btn>
      <v-btn variant="tonal" @click="openImport">Import Employees (Excel/CSV)</v-btn>
    </div>

    <v-table class="mt-4">
      <thead>
        <tr>
          <th style="width:80px">ID</th>
          <th>Name</th>
          <th>Email</th>
          <th style="width:120px">Active</th>
          <th style="width:260px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in rows" :key="u.id">
          <td>{{ u.id }}</td>
          <td>{{ u.name }}</td>
          <td>{{ u.email }}</td>
          <td>
            <v-chip :color="u.is_active ? 'green' : 'grey'" size="small" label>
              {{ u.is_active ? 'Y' : 'N' }}
            </v-chip>
          </td>
          <td class="d-flex" style="gap:8px">
            <v-btn size="small" variant="text" @click="openMap(u)">Map Employee</v-btn>

            <!-- SUPERADMIN 전용: 활성/비활성 토글 -->
            <v-btn
              v-if="isSuper"
              size="small"
              variant="tonal"
              color="red"
              v-show="u.is_active"
              @click="deactivate(u)"
            >
              Deactivate
            </v-btn>
            <v-btn
              v-if="isSuper"
              size="small"
              variant="tonal"
              color="green"
              v-show="!u.is_active"
              @click="activate(u)"
            >
              Activate
            </v-btn>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td colspan="5" class="text-center text-medium-emphasis py-6">No users</td>
        </tr>
      </tbody>
    </v-table>

    <div class="d-flex justify-center my-4">
      <v-pagination v-model="page" :length="pages" @update:modelValue="load" />
    </div>

    <v-alert v-if="msg" type="info" class="mt-2">{{ msg }}</v-alert>
    <v-alert v-if="err" type="warning" class="mt-2">{{ err }}</v-alert>

    <!-- Create User Dialog -->
    <v-dialog v-model="dlgCreate" max-width="480">
      <v-card>
        <v-card-title>New User</v-card-title>
        <v-card-text>
          <v-text-field v-model="newUser.name" label="Name" />
          <v-text-field v-model="newUser.email" label="Email" />
          <v-switch v-model="newUser.is_active" label="Active" inset />
          <div class="text-caption mt-2">* SUPERADMIN만 생성 가능합니다.</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlgCreate=false">Cancel</v-btn>
          <v-btn color="primary" @click="createUser">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Import Employees Dialog -->
    <v-dialog v-model="dlgImport" max-width="520">
      <v-card>
        <v-card-title>Import Employees (Excel/CSV)</v-card-title>
        <v-card-text>
          <div class="text-body-2 mb-2">
            헤더: <code>emp_no,name,dept,title</code> (UTF-8/CP949 자동)
          </div>
          <input type="file" ref="importRef" accept=".csv,.xlsx,.xls,.htm,.html" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlgImport=false">Close</v-btn>
          <v-btn color="primary" @click="doImport">Upload</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Map Employee Dialog -->
    <v-dialog v-model="dlgMap" max-width="720">
      <v-card>
        <v-card-title>Map Employee — {{ selUser?.name }} (ID: {{ selUser?.id }})</v-card-title>
        <v-card-text>
          <div class="d-flex align-center" style="gap:12px">
            <v-text-field
              v-model="empQ"
              label="Search employees"
              density="comfortable"
              hide-details
              clearable
              style="max-width:320px"
              @keyup.enter="loadEmployees(1)"
            />
            <v-btn @click="loadEmployees(1)">Search</v-btn>
          </div>
          <v-table class="mt-3">
            <thead>
              <tr>
                <th style="width:80px">ID</th>
                <th>EmpNo</th>
                <th>Name</th>
                <th>Dept/Title</th>
                <th style="width:120px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in empRows" :key="e.id">
                <td>{{ e.id }}</td>
                <td>{{ e.emp_no }}</td>
                <td>{{ e.name }}</td>
                <td>{{ e.dept }} / {{ e.title }}</td>
                <td><v-btn size="small" color="primary" @click="mapEmployee(e)">Select</v-btn></td>
              </tr>
              <tr v-if="!empRows.length">
                <td colspan="5" class="text-center text-medium-emphasis py-6">No employees</td>
              </tr>
            </tbody>
          </v-table>
          <div class="d-flex justify-center my-2">
            <v-pagination v-model="empPage" :length="empPages" @update:modelValue="loadEmployees" />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlgMap=false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'

type UserRow = { id:number; name:string; email:string; is_active:boolean; employee_id?:number|null }
type EmpRow  = { id:number; emp_no:string; name:string; dept:string; title:string }

const auth = useAuthStore()
const isSuper = computed(() =>
  !!auth?.hasRole?.('SUPERADMIN') || auth.user?.roles?.includes('SUPERADMIN')
)

const rows   = ref<UserRow[]>([])
const total  = ref(0)
const page   = ref(1)
const size   = ref(20)
const q      = ref('')
const err    = ref<string | null>(null)
const msg    = ref<string | null>(null)

const pages = computed(() => Math.max(1, Math.ceil(total.value / size.value)))

async function load(p = page.value) {
  err.value = null; msg.value = null
  page.value = p
  try {
    const data = await http.get<{ total:number; items:UserRow[]; page:number; size:number }>(
      `users?q=${encodeURIComponent(q.value)}&page=${p}&size=${size.value}`
    )
    rows.value  = data.items ?? []
    total.value = data.total ?? 0
  } catch (e:any) {
    rows.value = []; total.value = 0
    err.value = '사용자 목록 불러오기 실패'
  }
}
onMounted(() => load(1))

/* Create User (SUPERADMIN) */
const dlgCreate = ref(false)
const newUser   = ref({ name:'', email:'', is_active:true })
function openCreate(){
  newUser.value = { name:'', email:'', is_active:true }
  err.value=null; msg.value=null
  dlgCreate.value = true
}
async function createUser(){
  err.value = null; msg.value = null
  try{
    await http.post('users', newUser.value)
    dlgCreate.value = false
    await load(1)
  }catch(e:any){
    err.value = e?.detail ?? e?.message ?? '생성 실패(권한 필요: SUPERADMIN)'
  }
}

/* Import Employees (SUPERADMIN) */
const dlgImport = ref(false)
const importRef = ref<HTMLInputElement|null>(null)
function openImport(){
  err.value=null; msg.value=null
  if(importRef.value) importRef.value.value=''
  dlgImport.value = true
}
async function doImport(){
  const el = importRef.value
  if(!el || !el.files || !el.files[0]){ err.value = 'CSV 파일 선택'; return }
  try{
    const fd = new FormData()
    fd.append('file', el.files[0])
    const data = await http.post<{ok:boolean;created:number;updated:number}>('employees/import', fd)
    msg.value = `임포트 완료: +${data.created}, 수정 ${data.updated}`
  }catch(e:any){
    err.value = e?.detail ?? e?.message ?? '임포트 실패(권한 필요: SUPERADMIN)'
  }
}

/* Map Employee */
const dlgMap   = ref(false)
const selUser  = ref<UserRow | null>(null)
const empRows  = ref<EmpRow[]>([])
const empTotal = ref(0)
const empPage  = ref(1)
const empSize  = ref(10)
const empQ     = ref('')
const empPages = computed(() => Math.max(1, Math.ceil(empTotal.value / empSize.value)))

function openMap(u: UserRow){
  selUser.value = u
  err.value=null; msg.value=null
  dlgMap.value = true
  loadEmployees(1)
}
async function loadEmployees(p = empPage.value){
  empPage.value = p
  try{
    const data = await http.get<{ total:number; items:EmpRow[]; page:number; size:number }>(
      `employees?q=${encodeURIComponent(empQ.value)}&page=${p}&size=${empSize.value}`
    )
    empRows.value  = data.items ?? []
    empTotal.value = data.total ?? 0
  }catch{
    empRows.value = []; empTotal.value = 0
  }
}
async function mapEmployee(e: EmpRow){
  if(!selUser.value) return
  try{
    await http.put(`users/${selUser.value.id}/employee/${e.id}`)
    msg.value = `Mapped: ${selUser.value.name} → ${e.name} (${e.emp_no})`
  }catch{
    err.value = '사원 매핑 실패'
  }
}

/* Activate / Deactivate (SUPERADMIN) */
async function deactivate(u: UserRow){
  if(!isSuper.value) { err.value = '권한 없음'; return }
  if(!confirm(`정말 비활성화 하시겠습니까? (복구 가능)`)) return
  try{
    await http.delete(`users/${u.id}`)
    msg.value = `User #${u.id} 비활성화`
    await load(page.value)
  }catch(e:any){
    err.value = e?.detail ?? e?.message ?? '비활성화 실패'
  }
}
async function activate(u: UserRow){
  if(!isSuper.value) { err.value = '권한 없음'; return }
  try{
    await http.put(`users/${u.id}/approve`, { is_active: true })
    msg.value = `User #${u.id} 활성화`
    await load(page.value)
  }catch(e:any){
    err.value = e?.detail ?? e?.message ?? '활성화 실패'
  }
}
</script>

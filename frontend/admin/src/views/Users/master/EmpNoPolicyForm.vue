<!-- ============================================================================
# File      : src/views/Users/master/EmpNoPolicyForm.vue
# Version   : 2025.10-27 · v1.1 (Stabilized I/O · Better UX · Full Comments)
# Purpose   : Hotel Admin — '사번 정책' 단일 설정 전용 폼
# ----------------------------------------------------------------------------
# 배경/문제:
#   • MasterTable(리스트/CRUD 공통 컴포넌트)는 "다중 행" 기준정보에 적합.
#   • 사번 정책(EmpNoPolicy)은 "단일 정책(1 row)" 성격 → 리스트 컴포넌트로는 빈 목록/저장오류.
# 해법:
#   • 전용 폼 컴포넌트로 분리하여 단일 오브젝트를 GET/PUT(POST fallback)로만 다룬다.
#   • prefix / start_no / auto_increment / memo 를 관리(백엔드 스키마와 필드 동명 유지).
# ----------------------------------------------------------------------------
# API 계약(백엔드):
#   • GET  /api/master/empno-policy
#      → { id?, prefix, start_no, auto_increment, memo?, updated_at? } | 404/{} (환경에 따라)
#   • PUT  /api/master/empno-policy
#      → body: { prefix, start_no, auto_increment, memo }
#   • (옵션) POST /api/master/empno-policy  → 초기 생성 시 사용(서버 구현에 따라 미지원일 수 있음)
#   ※ 라우터 path는 하이픈(-): empno-policy  (언더바 아님)
# ----------------------------------------------------------------------------
# UX 노트:
#   • 저장 전/후 비교로 dirty 상태를 계산해 불필요한 저장을 방지.
#   • 로딩/에러 토스트 제공, 저장 후 재조회(load())로 일관성 확보.
#   • Prefix는 자동 대문자화, start_no는 0 이상의 정수만 허용.
# ----------------------------------------------------------------------------
# 트러블슈팅 팁:
#   [TIP-1] 404 또는 빈 {} 응답이면 DB 미초기화 상태 → 폼은 기본값을 표시하고 저장 시 PUT→POST 순으로 시도.
#   [TIP-2] 경로를 /api/master/empno_policy 로 호출하면 404 (언더바 금지, 하이픈 사용).
#   [TIP-3] NAS/프록시 환경에서 데이터가 안 보이면 APP_DB_URL(절대경로)과 Vite 프록시(/api→8001)를 점검.
# ============================================================================ -->
<template>
  <v-card flat class="rounded-xl elevation-1">
    <!-- 헤더 -->
    <v-card-title class="d-flex align-center gap-2">
      <v-icon color="cyan" size="22">mdi-badge-account</v-icon>
      <span class="font-weight-bold text-subtitle-1">사번 정책</span>
      <v-spacer />
      <v-btn
        variant="text"
        prepend-icon="mdi-refresh"
        @click="load"
        :loading="loading"
      >
        새로고침
      </v-btn>
    </v-card-title>

    <v-divider />

    <!-- 본문 폼 -->
    <v-card-text>
      <v-form ref="formRef" v-model="formValid" lazy-validation>
        <v-row dense>
          <!-- Prefix -->
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.prefix"
              label="Prefix"
              placeholder="예: EMP"
              :rules="[ruleRequired, rulePrefix]"
              @blur="form.prefix = (form.prefix || '').toUpperCase()"
              clearable
              hide-details="auto"
            />
          </v-col>

          <!-- 시작번호 -->
          <v-col cols="12" md="3">
            <v-text-field
              v-model.number="form.start_no"
              label="시작번호"
              type="number"
              :rules="[ruleRequired, rulePositive]"
              clearable
              hide-details="auto"
            />
          </v-col>

          <!-- 자동증가 -->
          <v-col cols="12" md="3" class="d-flex align-center">
            <v-switch
              v-model="form.auto_increment"
              inset
              color="primary"
              hide-details
              label="자동 증가 사용"
            />
          </v-col>

          <!-- 메모 -->
          <v-col cols="12">
            <v-textarea
              v-model="form.memo"
              label="메모"
              auto-grow
              rows="2"
              clearable
              hide-details="auto"
            />
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>

    <v-divider />

    <!-- 액션 -->
    <v-card-actions>
      <v-spacer />
      <v-btn
        variant="text"
        @click="reset"
        :disabled="loading || !dirty"
      >
        되돌리기
      </v-btn>
      <v-btn
        color="primary"
        @click="save"
        :loading="loading"
        :disabled="!formValid || !dirty"
        prepend-icon="mdi-content-save"
      >
        저장
      </v-btn>
    </v-card-actions>

    <!-- 로딩 인디케이터 -->
    <v-progress-linear v-if="loading" indeterminate />
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
const { success, error } = useToast()

/** 백엔드 라우터는 하이픈(-) 경로. http.ts 가 '/api' prefix 자동 부착 */
const API = 'master/empno-policy'

/** 폼 스키마 (백엔드와 동명 유지) */
type Policy = {
  id?: number
  prefix: string
  start_no: number
  auto_increment: boolean
  memo?: string
}

const loading   = ref(false)
const formRef   = ref()
const formValid = ref(false)

/** 안전 기본값 */
const form = ref<Policy>({
  prefix: 'EMP',
  start_no: 1,
  auto_increment: true,
  memo: '',
})

/** 원본 스냅샷 — dirty 계산용 */
const original = ref<Policy>({ ...form.value })

/** 유효성 */
const ruleRequired = (v: any) => (!!v || v === 0) || '필수 입력입니다.'
const rulePositive = (v: number) => (Number.isInteger(v) && v >= 0) || '0 이상의 정수'
const rulePrefix   = (v: string) => /^[A-Z0-9_]+$/.test(v || '') || '영문 대문자/숫자/_만 허용'

/** 변경 여부 — JSON 비교(간단/안전) */
const dirty = computed(() => JSON.stringify(form.value) !== JSON.stringify(original.value))

/** 단일 정책 로드 */
async function load() {
  loading.value = true
  try {
    const res: any = await http.get(API) // GET /api/master/empno-policy
    if (res && typeof res === 'object') {
      form.value = {
        id: res.id,
        prefix: (res.prefix ?? 'EMP').toUpperCase(),
        start_no: Number(res.start_no ?? 1),
        auto_increment: !!(res.auto_increment ?? true),
        memo: res.memo ?? '',
      }
      original.value = { ...form.value }
    } else {
      // 404/{} 케이스: 기본값 유지
      form.value     = { prefix: 'EMP', start_no: 1, auto_increment: true, memo: '' }
      original.value = { ...form.value }
    }
  } catch (e) {
    // GET 실패 → 기본값 유지 + 토스트
    error('사번 정책 불러오기 실패 (기본값으로 표시)')
  } finally {
    loading.value = false
  }
}

/** 저장 — 표준은 PUT, 실패 시 POST로 초기 생성 시도 */
async function save() {
  const ok = await (formRef.value as any)?.validate?.()
  if (!ok?.valid) return

  loading.value = true
  try {
    const payload = {
      prefix: (form.value.prefix || 'EMP').toUpperCase(),
      start_no: Number(form.value.start_no || 1),
      auto_increment: !!form.value.auto_increment,
      memo: form.value.memo || '',
    }

    try {
      await http.put(API, payload)   // PUT /api/master/empno-policy
    } catch {
      await http.post(API, payload)  // POST fallback (초기 생성)
    }

    success('사번 정책이 저장되었습니다.')
    await load() // 저장 후 재조회로 폼/원본 동기화
  } catch (e) {
    error('사번 정책 저장 실패')
  } finally {
    loading.value = false
  }
}

/** 되돌리기 */
function reset() {
  form.value = { ...original.value }
}

/** 최초 로드 */
load()
</script>

<style scoped>
.page-shell { max-width: 1280px; margin: 0 auto; }
</style>

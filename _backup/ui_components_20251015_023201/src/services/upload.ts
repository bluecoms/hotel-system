// src/services/upload.ts
import http from '@/services/http'

/** BE 응답 스키마 (드라이런) */
export type UploadDryRunResponse = {
  ok: true
  dry_run: true
  received: number
  inserted: 0
  errors: { row: number; message: string }[]
}

/** BE 응답 스키마 (적용 성공) */
export type UploadSuccessResponse = {
  ok: true
  session_id: string
  version_no: number
}

export type UploadResponse = UploadDryRunResponse | UploadSuccessResponse

/**
 * sales_front 업로드
 * @param file 업로드할 CSV 파일
 * @param propertyCode 필수. 예: 'MOP'
 * @param dryRun 기본 true. true면 검증만, false면 실제 반영
 */
export async function uploadSalesFront(
  file: File,
  propertyCode: string,
  dryRun: boolean = true
): Promise<UploadResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('property_code', propertyCode)         // 필수
  fd.append('dry_run', dryRun ? '1' : '0')         // 1"/"0" 문자열

  // 엔드포인트는 /api prefix 사용
  return await http.post<UploadResponse>('/api/upload/sales_front', fd)
}

/** 타입 가드: 드라이런 응답인지 식별 */
export function isUploadDryRun(res: UploadResponse): res is UploadDryRunResponse {
  return (res as UploadDryRunResponse)?.dry_run === true
}

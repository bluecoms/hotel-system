// src/services/employees.ts
import http from '@/services/http'

export async function getEmployee(id: number){
  return await http.get(`/employees/${id}`)
}

export async function saveEmployee(id: number, patch: any){
  return await http.put(`/employees/${id}`, patch)
}

export async function mapUserEmployee(userId: number, empId: number){
  return await http.put(`/users/${userId}/employee/${empId}`)
}

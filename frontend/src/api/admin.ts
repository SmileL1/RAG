import { http } from './client'

export interface AdminUser {
  id: number
  username: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface CreateUserPayload {
  username: string
  password?: string
  is_admin?: boolean
}

export interface CreateUserResult {
  user: AdminUser
  generated_password: string | null
}

export const adminApi = {
  listUsers: () =>
    http.get<AdminUser[]>('/admin/users').then((r) => r.data),

  createUser: (payload: CreateUserPayload) =>
    http.post<CreateUserResult>('/admin/users', payload).then((r) => r.data),

  updateUser: (id: number, payload: { is_active?: boolean; is_admin?: boolean }) =>
    http.patch<AdminUser>(`/admin/users/${id}`, payload).then((r) => r.data),

  resetPassword: (id: number) =>
    http.post<CreateUserResult>(`/admin/users/${id}/reset-password`).then((r) => r.data),

  deleteUser: (id: number) =>
    http.delete<{ message: string }>(`/admin/users/${id}`).then((r) => r.data),
}

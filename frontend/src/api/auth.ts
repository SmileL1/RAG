import { http } from './client'

export const authApi = {
  login: (username: string, password: string) =>
    http
      .post<{ access_token: string; token_type: string }>('/auth/login', { username, password })
      .then((r) => r.data),

  me: () =>
    http
      .get<{ id: number; username: string; is_active: boolean }>('/auth/me')
      .then((r) => r.data),

  changePassword: (oldPassword: string, newPassword: string) =>
    http.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
}

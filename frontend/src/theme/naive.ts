/* Naive UI 主题覆盖：蓝白亮色系 */
import type { GlobalThemeOverrides } from 'naive-ui'

export const naiveDarkOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2563EB',
    primaryColorHover: '#3B82F6',
    primaryColorPressed: '#1D4ED8',
    primaryColorSuppl: '#0EA5E9',

    infoColor: '#0EA5E9',
    successColor: '#10B981',
    warningColor: '#F59E0B',
    errorColor: '#EF4444',

    bodyColor: 'transparent',
    cardColor: 'rgba(255, 255, 255, 0.88)',
    modalColor: '#FFFFFF',
    popoverColor: '#FFFFFF',

    textColor1: '#0F172A',
    textColor2: '#475569',
    textColor3: '#94A3B8',

    borderRadius: '12px',
    borderColor: 'rgba(37, 99, 235, 0.12)',

    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif',
  },
  Button: {
    borderRadiusMedium: '10px',
    fontWeightStrong: '600',
  },
  Card: {
    borderRadius: '20px',
    paddingMedium: '20px 24px',
    color: 'rgba(255, 255, 255, 0.88)',
    borderColor: 'rgba(37, 99, 235, 0.10)',
  },
  Input: {
    borderRadius: '12px',
    color: '#FFFFFF',
    borderColor: 'rgba(37, 99, 235, 0.15)',
    borderFocusColor: '#2563EB',
  },
  Menu: {
    itemHeight: '44px',
    borderRadius: '10px',
    itemTextColor: '#475569',
    itemTextColorActive: '#2563EB',
    itemTextColorHover: '#0F172A',
    itemColorActive: 'rgba(37, 99, 235, 0.10)',
    itemColorHover: 'rgba(37, 99, 235, 0.06)',
    color: 'transparent',
  },
  Modal: {
    color: '#FFFFFF',
    borderRadius: '20px',
  },
}

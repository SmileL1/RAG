/* Naive UI 主题覆盖：当代 SaaS 亮色系（深紫罗兰 accent） */
import type { GlobalThemeOverrides } from 'naive-ui'

export const naiveDarkOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#5B4FE8',
    primaryColorHover: '#4A3FD4',
    primaryColorPressed: '#3F35BE',
    primaryColorSuppl: '#6A5FF0',

    infoColor: '#5B4FE8',
    successColor: '#0E9F6E',
    warningColor: '#F59E0B',
    errorColor: '#EF4444',

    bodyColor: 'transparent',
    cardColor: '#FFFFFF',
    modalColor: '#FFFFFF',
    popoverColor: '#FFFFFF',

    textColor1: '#15161B',
    textColor2: '#4B4F5A',
    textColor3: '#9498A4',

    borderRadius: '12px',
    borderColor: '#ECEDF1',

    fontFamily:
      "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif",
  },
  Button: {
    borderRadiusMedium: '10px',
    fontWeightStrong: '700',
  },
  Card: {
    borderRadius: '16px',
    paddingMedium: '20px 24px',
    color: '#FFFFFF',
    borderColor: '#ECEDF1',
  },
  Input: {
    borderRadius: '10px',
    color: '#FFFFFF',
    borderColor: '#E2E4EA',
    borderFocusColor: '#5B4FE8',
  },
  Menu: {
    itemHeight: '44px',
    borderRadius: '10px',
    itemTextColor: '#4B4F5A',
    itemTextColorActive: '#5B4FE8',
    itemTextColorActiveHover: '#4A3FD4',
    itemTextColorHover: '#15161B',
    itemColorActive: '#EEECFD',
    itemColorActiveHover: '#EEECFD',
    itemColorHover: '#F2F2F8',
    color: 'transparent',
  },
  Modal: {
    color: '#FFFFFF',
    borderRadius: '18px',
  },
}

import { defineConfig, presetAttributify, presetIcons, presetUno } from 'unocss';
export default defineConfig({
    presets: [
        presetUno(),
        presetAttributify(),
        presetIcons({
            scale: 1.2,
            cdn: 'https://esm.sh/',
        }),
    ],
    theme: {
        colors: {
            bg: {
                primary: '#0B0E1A',
                secondary: '#12172A',
                elevated: 'rgba(255, 255, 255, 0.06)',
            },
            brand: {
                purple: '#7B61FF',
                cyan: '#00D4FF',
            },
            cta: {
                gold: '#FFB800',
                orange: '#FF6B35',
            },
            text: {
                primary: '#FFFFFF',
                secondary: '#A0A6C2',
                muted: '#6B7190',
            },
            success: '#00E5A0',
            warning: '#FFB800',
            error: '#FF4D6E',
        },
        boxShadow: {
            glass: '0 8px 32px rgba(0, 0, 0, 0.4)',
            neon: '0 0 24px rgba(123, 97, 255, 0.3)',
            'neon-cyan': '0 0 24px rgba(0, 212, 255, 0.3)',
        },
    },
    shortcuts: {
        'glass-card': 'bg-bg-elevated backdrop-blur-12 border border-white/8 rounded-2xl shadow-glass',
        'brand-gradient': 'bg-gradient-to-br from-brand-purple to-brand-cyan',
        'cta-gradient': 'bg-gradient-to-r from-cta-gold to-cta-orange',
        'text-gradient': 'bg-gradient-to-br from-brand-purple to-brand-cyan bg-clip-text text-transparent',
    },
});

import { createI18n } from 'vue-i18n'
import cs from './locales/cs.json'
import en from './locales/en.json'

export type MessageSchema = typeof cs

const i18n = createI18n<[MessageSchema], 'cs' | 'en'>({
  legacy: false,
  locale: 'cs',
  fallbackLocale: 'en',
  messages: {
    cs,
    en,
  },
})

export default i18n

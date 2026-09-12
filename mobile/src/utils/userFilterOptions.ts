import type { ProfileOption } from '@/types/api'

export type UserFilterOption = {
  value: string
  label: string
}

const ukrainianCollator = new Intl.Collator('uk-UA', { sensitivity: 'base' })

export function userFilterLabel(profile: ProfileOption, fallback: string) {
  const user = profile.user_detail
  if (!user) return `${fallback} #${profile.id}`
  return [user.last_name, user.first_name].filter(Boolean).join(' ')
    || user.telegram_username
    || user.email
    || `${fallback} #${profile.id}`
}

export function userFilterOptions(
  profiles: ProfileOption[],
  allLabel: string,
  fallback: string,
): UserFilterOption[] {
  const options = profiles
    .map((profile) => ({ value: String(profile.id), label: userFilterLabel(profile, fallback) }))
    .sort((left, right) => ukrainianCollator.compare(left.label, right.label))

  return [{ value: '', label: allLabel }, ...options]
}

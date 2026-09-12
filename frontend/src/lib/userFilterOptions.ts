type UserDetails = {
  first_name?: string
  last_name?: string
  telegram_username?: string
  email?: string
}

type ProfileOption = {
  id: number
  user_detail?: UserDetails
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

export function sortFilterOptions<T extends { label: string }>(options: T[]) {
  return [...options].sort((left, right) => ukrainianCollator.compare(left.label, right.label))
}

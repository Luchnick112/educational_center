import { describe, expect, it } from 'vitest'
import { sortFilterOptions, userFilterLabel } from '@/lib/userFilterOptions'

describe('user filter options', () => {
  it('shows the last name first', () => {
    expect(userFilterLabel({
      id: 1,
      user_detail: { first_name: 'Олена', last_name: 'Бондар' },
    }, 'Учень')).toBe('Бондар Олена')
  })

  it('sorts labels with the Ukrainian collator', () => {
    const options = sortFilterOptions([
      { value: 2, label: 'Яремчук Анна' },
      { value: 1, label: 'Андрусенко Олег' },
    ])

    expect(options.map((option) => option.value)).toEqual([1, 2])
  })
})

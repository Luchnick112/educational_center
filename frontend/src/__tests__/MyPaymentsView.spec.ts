import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'

import { apiRequest } from '@/lib/api'
import SearchableSelect from '@/components/SearchableSelect.vue'
import MyPaymentsView from '@/views/MyPaymentsView.vue'

vi.mock('@/lib/api', () => ({ apiRequest: vi.fn() }))
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    me: { role: 'admin', is_staff: true },
    bootstrap: vi.fn().mockResolvedValue(undefined),
    refreshMe: vi.fn().mockResolvedValue(undefined),
  }),
}))

const mockedApiRequest = vi.mocked(apiRequest)
let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  vi.clearAllMocks()
})

describe('MyPaymentsView', () => {
  it('orders and searches payment recipients by surname', async () => {
    mockedApiRequest.mockImplementation(async (path) => {
      if (path === '/api/users/students/') {
        return [
          { id: 2, user_detail: { first_name: 'Анна', last_name: 'Яремчук' } },
          { id: 1, user_detail: { first_name: 'Олег', last_name: 'Андрусенко' } },
        ] as never
      }
      if (path === '/api/users/teachers/') {
        return [
          { id: 2, user_detail: { first_name: 'Анна', last_name: 'Яремчук' } },
          { id: 1, user_detail: { first_name: 'Олег', last_name: 'Андрусенко' } },
        ] as never
      }
      return {
        charges: [],
        payouts: [],
        student_payments: [],
        teacher_payments: [],
        student_summaries: [],
        teacher_summaries: [],
      } as never
    })

    wrapper = mount(MyPaymentsView, {
      global: {
        stubs: {
          AppShell: { template: '<main><slot /></main>' },
          DataTable: { template: '<div />' },
        },
      },
    })
    await flushPromises()

    const teacherSelects = wrapper.findAllComponents(SearchableSelect)
      .filter((select) => select.props('label') === 'Викладач')
    expect(teacherSelects).toHaveLength(2)
    expect(teacherSelects[1]?.props('options').map((option: { label: string }) => option.label)).toEqual([
      'Оберіть викладача',
      'Андрусенко Олег',
      'Яремчук Анна',
    ])

    const paymentSelect = teacherSelects[1]
    if (!paymentSelect) throw new Error('Payment recipient select not found')
    await paymentSelect.get('.searchable-select__trigger').trigger('click')
    await paymentSelect.get<HTMLInputElement>('.searchable-select__search').setValue('яремчук')
    expect(paymentSelect.findAll('.searchable-select__option').map((option) => option.text())).toEqual(['Яремчук Анна'])
  })
})

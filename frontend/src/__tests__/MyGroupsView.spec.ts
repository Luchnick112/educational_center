import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'

import { apiRequest } from '@/lib/api'
import MyGroupsView from '@/views/MyGroupsView.vue'

vi.mock('@/lib/api', () => ({ apiRequest: vi.fn() }))
vi.mock('@/lib/detailRoute', () => ({
  pushDetailRoute: vi.fn().mockResolvedValue(false),
  replaceWithoutDetailRoute: vi.fn().mockResolvedValue(undefined),
  routeQueryId: vi.fn().mockReturnValue(null),
}))
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    me: { role: 'admin', is_staff: true },
    bootstrap: vi.fn().mockResolvedValue(undefined),
  }),
}))
vi.mock('vue-router', () => ({
  useRoute: () => ({ name: 'my-groups', query: {} }),
  useRouter: () => ({ push: vi.fn().mockResolvedValue(undefined) }),
}))

const mockedApiRequest = vi.mocked(apiRequest)
let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  document.body.style.overflow = ''
  vi.clearAllMocks()
})

describe('MyGroupsView', () => {
  it('opens group details and editing in modal dialogs', async () => {
    mockedApiRequest.mockImplementation(async (path) => {
      if (path === '/api/academics/subjects/') return [{ id: 1, name: 'Математика' }] as never
      if (path === '/api/academics/groups/') {
        return [
          {
            id: 7,
            name: 'Математика 7',
            teacher: 3,
            subject: 1,
            format: 'group',
            student_price: '500.00',
            teacher_rate: '300.00',
          },
        ] as never
      }
      return [] as never
    })

    wrapper = mount(MyGroupsView, {
      global: {
        stubs: {
          AppShell: { template: '<main><slot /></main>' },
        },
      },
    })
    await flushPromises()

    await wrapper.get('.groups-table tbody tr').trigger('click')
    await flushPromises()

    expect(wrapper.get('.group-detail-modal').attributes('role')).toBe('dialog')
    expect(wrapper.get('#group-detail-title').text()).toBe('Математика 7')
    expect(document.body.style.overflow).toBe('hidden')

    await wrapper.get('.group-detail__actions .btn').trigger('click')
    await flushPromises()

    expect(wrapper.find('.group-detail-modal').exists()).toBe(false)
    expect(wrapper.get('.group-edit-modal').attributes('role')).toBe('dialog')
    expect(wrapper.get('#group-edit-title').text()).toContain('Математика 7')
  })
})

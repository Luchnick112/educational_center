import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import SearchableSelect from '@/components/SearchableSelect.vue'

describe('SearchableSelect', () => {
  it('searches options and emits the selected value', async () => {
    const wrapper = mount(SearchableSelect, {
      attachTo: document.body,
      props: {
        label: 'Учні',
        modelValue: null,
        options: [
          { value: null, label: 'Всі учні' },
          { value: 1, label: 'Анна Коваль' },
          { value: 2, label: 'Олег Бондар' },
        ],
      },
    })

    await wrapper.get('.searchable-select__trigger').trigger('click')

    const search = wrapper.get<HTMLInputElement>('.searchable-select__search')
    expect(document.activeElement).toBe(search.element)

    await search.setValue('олег')
    const options = wrapper.findAll('.searchable-select__option')
    expect(options).toHaveLength(1)
    expect(options[0].text()).toBe('Олег Бондар')

    await options[0].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([[2]])
    expect(wrapper.emitted('change')).toHaveLength(1)
    expect(wrapper.find('.searchable-select__menu').exists()).toBe(false)

    wrapper.unmount()
  })
})

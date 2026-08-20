import type { RouteLocationNormalizedLoaded, Router } from 'vue-router'

export function routeQueryValue(route: RouteLocationNormalizedLoaded, key: string) {
  const value = route.query[key]
  return Array.isArray(value) ? value[0] : value
}

export function routeQueryId(route: RouteLocationNormalizedLoaded, key: string) {
  const value = routeQueryValue(route, key)
  if (!value) return null

  const id = Number(value)
  return Number.isInteger(id) && id > 0 ? id : null
}

export async function pushDetailRoute(router: Router, route: RouteLocationNormalizedLoaded, key: string, id: number) {
  if (routeQueryValue(route, key) === String(id)) return false

  await router.push({
    name: route.name || undefined,
    query: {
      ...route.query,
      [key]: String(id),
    },
  })
  return true
}

export async function replaceWithoutDetailRoute(
  router: Router,
  route: RouteLocationNormalizedLoaded,
  fallbackRouteName: string,
  key: string,
) {
  const query = { ...route.query }
  delete query[key]

  await router.replace({
    name: route.name || fallbackRouteName,
    query,
  })
}

export type UserRole = 'admin' | 'teacher' | 'student' | 'parent' | string

export type MeResponse = {
  id: number
  first_name: string
  last_name: string
  telegram_username?: string
  email: string
  phone?: string
  role: UserRole
  is_staff: boolean
  my?: Array<{ key: string; url: string }>
}

export type Lesson = {
  id: number
  status: string
  starts_at: string
  notes?: string
  group: number
  payroll_amount?: string
  billed_amount?: string
}

export type LessonPage = {
  count: number
  page: number
  page_size: number
  results: Lesson[]
}

export type StudyGroup = {
  id: number
  name?: string
  format?: string | null
  capacity?: number | null
  completed_lessons_count?: number | null
  lessons_until_next_billing?: number | null
}

export type Student = {
  id: number
  user_detail?: {
    first_name?: string
    last_name?: string
    email?: string
    telegram_username?: string
  }
}

export type Charge = {
  id: number
  status: string
  amount: string
  student_name?: string
  lesson_starts_at?: string
  issued_at?: string
  paid_at?: string | null
}

export type Payout = {
  id: number
  status: string
  amount: string
  teacher_name?: string
  student_name?: string
  lesson_starts_at?: string
}

export type StudentSummary = {
  student: number
  student_name: string
  charged_amount: string
  paid_amount: string
  debt_amount: string
}

export type TeacherSummary = {
  teacher: number
  teacher_name: string
  accrued_amount: string
  paid_amount: string
  debt_amount: string
}

export type PaymentsResponse = {
  charges?: Charge[]
  payouts?: Payout[]
  student_summaries?: StudentSummary[]
  teacher_summaries?: TeacherSummary[]
}

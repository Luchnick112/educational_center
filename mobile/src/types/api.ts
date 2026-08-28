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

export type UserAccount = {
  id: number
  first_name: string
  last_name: string
  telegram_username?: string | null
  email: string
  phone?: string
  role: UserRole
  is_active: boolean
}

export type Lesson = {
  id: number
  status: string
  starts_at: string
  notes?: string
  group: number
  payroll_amount?: string
  billed_amount?: string
  can_request_reschedule?: boolean
  participants?: LessonParticipant[]
}

export type LessonParticipant = {
  id: number
  student: number
  student_first_name?: string
  student_last_name?: string
  attendance_status: 'pending' | 'present' | 'absent' | string
  billed_amount?: string
  payroll_amount?: string
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
  subject?: number
  teacher?: number | null
  student_price?: string
  teacher_rate?: string
  is_active?: boolean
}

export type Subject = {
  id: number
  name: string
}

export type ProfileOption = {
  id: number
  user_detail?: {
    first_name?: string
    last_name?: string
    email?: string
    telegram_username?: string
  }
}

export type Enrollment = {
  id: number
  group: number
  student: number
  status: string
  end_date?: string | null
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
  student?: number
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
  teacher?: number
}

export type StudentPayment = {
  id: number
  student: number
  student_name?: string
  amount: string
  paid_at: string
  comment?: string
}

export type TeacherPayment = {
  id: number
  teacher: number
  teacher_name?: string
  amount: string
  paid_at: string
  comment?: string
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
  student_payments?: StudentPayment[]
  teacher_payments?: TeacherPayment[]
}

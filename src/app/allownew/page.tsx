"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  MousePointer,
  Monitor,
  Terminal,
  HardDrive,
  Settings,
  Shield,
  Mic,
  Calendar,
  Bell,
  Key,
  Check,
  ChevronDown,
  Play,
  Image,
  Video
} from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface Permission {
  id: string
  title: string
  description: string
  detailedDescription: string
  icon: React.ComponentType<{ className?: string }>
  priority: 'critical' | 'automation' | 'user'
  status: 'granted' | 'denied' | 'pending'
  mediaType: 'video' | 'image' | 'demo'
  mediaUrl: string
  instructions: string[]
}

const permissions: Permission[] = [
  {
    id: 'accessibility',
    title: 'Accessibility',
    description: 'Позволяет AI агенту управлять курсором и клавиатурой',
    detailedDescription: 'Критически важно! Это разрешение позволяет AI агенту полностью взаимодействовать с вашим Mac: перемещать курсор, выполнять клики, вводить текст и управлять всеми элементами интерфейса.',
    icon: MousePointer,
    priority: 'critical',
    status: 'pending',
    mediaType: 'video',
    mediaUrl: '/demo/accessibility-demo.mp4',
    instructions: [
      'Откройте Системные настройки',
      'Перейдите в Конфиденциальность и безопасность',
      'Выберите Универсальный доступ',
      'Добавьте Skygen и включите переключатель'
    ]
  },
  {
    id: 'screen-recording',
    title: 'Screen Recording',
    description: 'Необходимо для анализа содержимого экрана',
    detailedDescription: 'AI агент сможет видеть содержимое вашего экрана, создавать скриншоты и понимать контекст для более точного выполнения задач.',
    icon: Monitor,
    priority: 'critical',
    status: 'pending',
    mediaType: 'image',
    mediaUrl: '/demo/screen-recording-setup.png',
    instructions: [
      'Откройте Системные настройки',
      'Перейдите в Конфиденциальность и безопасность',
      'Выберите Запись экрана',
      'Добавьте Skygen в список разрешенных приложений'
    ]
  },
  {
    id: 'full-disk',
    title: 'Full Disk Access',
    description: 'Доступ к файлам и папкам системы',
    detailedDescription: 'Позволяет AI агенту читать, создавать и изменять файлы во всех папках, включая защищенные системные директории.',
    icon: HardDrive,
    priority: 'critical',
    status: 'pending',
    mediaType: 'demo',
    mediaUrl: '',
    instructions: [
      'Откройте Системные настройки',
      'Перейдите в Конфиденциальность и безопасность',
      'Выберите Полный доступ к диску',
      'Добавьте Skygen и включите доступ'
    ]
  },
  {
    id: 'automation',
    title: 'Automation',
    description: 'AppleScript и автоматизация системы',
    detailedDescription: 'Разрешает использование AppleScript и Automator для автоматизации сложных системных процессов и управления приложениями.',
    icon: Settings,
    priority: 'automation',
    status: 'pending',
    mediaType: 'video',
    mediaUrl: '/demo/automation-demo.mp4',
    instructions: [
      'При первом запросе выберите "Разрешить"',
      'Или откройте Системные настройки',
      'Перейдите в Конфиденциальность и безопасность',
      'Выберите Automation и настройте разрешения'
    ]
  },
  {
    id: 'terminal',
    title: 'Terminal Access',
    description: 'Выполнение команд в терминале',
    detailedDescription: 'AI агент сможет выполнять команды в Terminal для управления системой, установки программ и выполнения системных задач.',
    icon: Terminal,
    priority: 'automation',
    status: 'pending',
    mediaType: 'demo',
    mediaUrl: '',
    instructions: [
      'Разрешение предоставляется автоматически',
      'При необходимости введите пароль администратора',
      'Убедитесь, что Terminal имеет права на выполнение команд'
    ]
  },
  {
    id: 'microphone',
    title: 'Microphone Access',
    description: 'Голосовые команды и диктовка',
    detailedDescription: 'Позволяет AI агенту записывать аудио для голосовых команд, диктовки текста и других аудио-функций.',
    icon: Mic,
    priority: 'user',
    status: 'pending',
    mediaType: 'image',
    mediaUrl: '/demo/microphone-setup.png',
    instructions: [
      'Откройте Системные настройки',
      'Перейдите в Конфиденциальность и безопасность',
      'Выберите Микрофон',
      'Добавьте Skygen в список разрешенных приложений'
    ]
  }
]

const PermissionCard = ({ permission, isExpanded, onToggle, onGrant }: {
  permission: Permission
  isExpanded: boolean
  onToggle: () => void
  onGrant: () => void
}) => {
  const IconComponent = permission.icon
  
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'border-red-200'
      case 'automation': return 'border-blue-200'
      case 'user': return 'border-green-200'
      default: return 'border-gray-200'
    }
  }

  return (
    <motion.div
      layout
      className={cn(
        "bg-white border rounded-lg overflow-hidden cursor-pointer transition-all duration-300 aspect-[3/2]",
        getPriorityColor(permission.priority),
        isExpanded ? "shadow-lg" : "shadow-sm hover:shadow-md"
      )}
      onClick={!isExpanded ? onToggle : undefined}
    >
      {/* Media Section - Only when expanded */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: '50%', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ 
              duration: 0.25, 
              ease: "easeOut"
            }}
            className="bg-gradient-to-br from-blue-50 to-blue-100 border-b border-gray-200"
          >
            <div className="flex items-center justify-center h-full">
              {permission.mediaType === 'video' && (
                <div className="text-center">
                  <div className="w-16 h-10 bg-gray-800 rounded-lg flex items-center justify-center mb-1">
                    <Play className="w-6 h-6 text-white" />
                  </div>
                  <p className="text-xs text-gray-500">Demo Video</p>
                </div>
              )}
              {permission.mediaType === 'image' && (
                <div className="text-center">
                  <div className="w-16 h-10 bg-gray-200 rounded-lg flex items-center justify-center mb-1">
                    <Image className="w-6 h-6 text-gray-500" />
                  </div>
                  <p className="text-xs text-gray-500">Screenshot</p>
                </div>
              )}
              {permission.mediaType === 'demo' && (
                <div className="text-center">
                  <div className="w-16 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mb-1">
                    <Settings className="w-6 h-6 text-white animate-spin" />
                  </div>
                  <p className="text-xs text-gray-500">Interactive Demo</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Text Section - Always present */}
      <div className={cn(
        "p-3 flex flex-col justify-center",
        isExpanded ? "h-1/2" : "h-full"
      )}>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <IconComponent className="w-4 h-4 text-gray-600" />
          </div>
          <div className={cn(
            "w-2 h-2 rounded-full",
            permission.status === 'granted' ? 'bg-green-500' :
            permission.status === 'denied' ? 'bg-red-500' : 'bg-yellow-500'
          )} />
        </div>
        
        <h3 className="font-medium text-gray-900 mb-1 text-sm">
          {permission.title}
        </h3>
        <p className="text-gray-500 text-xs leading-tight mb-2">
          {permission.description}
        </p>

        {isExpanded && (
          <Button
            onClick={(e) => {
              e.stopPropagation()
              onGrant()
            }}
            disabled={permission.status === 'granted'}
            className={cn(
              "w-full mt-2",
              permission.status === 'granted' 
                ? "bg-green-600 hover:bg-green-700" 
                : "bg-blue-600 hover:bg-blue-700"
            )}
            size="sm"
          >
            {permission.status === 'granted' ? (
              <>
                <Check className="w-3 h-3 mr-1" />
                Granted
              </>
            ) : (
              'Grant Permission'
            )}
          </Button>
        )}
      </div>
    </motion.div>
  )
}

export default function AllowNewPage() {
  const [permissionsList, setPermissionsList] = useState(permissions)
  const [expandedCard, setExpandedCard] = useState<string | null>(null)

  const handleToggleCard = (id: string) => {
    setExpandedCard(expandedCard === id ? null : id)
  }

  const handleGrantPermission = (id: string) => {
    setPermissionsList(prev => 
      prev.map(permission => 
        permission.id === id 
          ? { ...permission, status: 'granted' as const }
          : permission
      )
    )
  }

  const groupedPermissions = {
    critical: permissionsList.filter(p => p.priority === 'critical'),
    automation: permissionsList.filter(p => p.priority === 'automation'),
    user: permissionsList.filter(p => p.priority === 'user')
  }

  const grantedCount = permissionsList.filter(p => p.status === 'granted').length
  const totalCount = permissionsList.length

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            System Permissions Setup
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            Configure permissions for Skygen AI Agent to work properly on your Mac
          </p>
          
          {/* Progress */}
          <div className="bg-white rounded-lg p-4 inline-block shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">Progress:</span>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(grantedCount / totalCount) * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-900">
                {grantedCount}/{totalCount}
              </span>
            </div>
          </div>
        </div>

        {/* Critical Permissions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            Critical Permissions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {groupedPermissions.critical.map(permission => (
              <PermissionCard
                key={permission.id}
                permission={permission}
                isExpanded={expandedCard === permission.id}
                onToggle={() => handleToggleCard(permission.id)}
                onGrant={() => handleGrantPermission(permission.id)}
              />
            ))}
          </div>
        </div>

        {/* Automation Permissions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            Automation
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {groupedPermissions.automation.map(permission => (
              <PermissionCard
                key={permission.id}
                permission={permission}
                isExpanded={expandedCard === permission.id}
                onToggle={() => handleToggleCard(permission.id)}
                onGrant={() => handleGrantPermission(permission.id)}
              />
            ))}
          </div>
        </div>

        {/* User Permissions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            User Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {groupedPermissions.user.map(permission => (
              <PermissionCard
                key={permission.id}
                permission={permission}
                isExpanded={expandedCard === permission.id}
                onToggle={() => handleToggleCard(permission.id)}
                onGrant={() => handleGrantPermission(permission.id)}
              />
            ))}
          </div>
        </div>

        {/* Continue Button */}
        <div className="text-center">
          <Button
            asChild
            size="lg"
            className={cn(
              "px-8 py-3 text-lg",
              grantedCount === totalCount
                ? "bg-green-600 hover:bg-green-700"
                : "bg-gray-400 cursor-not-allowed"
            )}
            disabled={grantedCount !== totalCount}
          >
            <Link href="/app">
              {grantedCount === totalCount ? (
                'Continue to App'
              ) : (
                `Grant ${totalCount - grantedCount} more permissions`
              )}
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

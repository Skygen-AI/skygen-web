"use client";

import React, { useState } from "react";
import { 
  User, 
  Lock, 
  Bell, 
  Palette, 
  Globe, 
  Shield, 
  CreditCard, 
  Zap,
  HelpCircle,
  Settings as SettingsIcon,
  ChevronRight,
  Save,
  X
} from "lucide-react";
import { Sidebar, SidebarBody, SidebarLink } from "../../components/ui/sidebar";
import { Wind } from "lucide-react";

interface SettingsSection {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
}

const settingsSections: SettingsSection[] = [
  {
    id: "profile",
    title: "Profile",
    subtitle: "Manage personal information",
    icon: <User size={20} />
  },
  {
    id: "privacy",
    title: "Privacy",
    subtitle: "Privacy and security settings",
    icon: <Lock size={20} />
  },
  {
    id: "notifications",
    title: "Notifications",
    subtitle: "Notification preferences",
    icon: <Bell size={20} />
  },
  {
    id: "appearance",
    title: "Appearance",
    subtitle: "Themes and display options",
    icon: <Palette size={20} />
  },
  {
    id: "language",
    title: "Language & Region",
    subtitle: "Localization and timezone",
    icon: <Globe size={20} />
  },
  {
    id: "security",
    title: "Security",
    subtitle: "Two-factor authentication",
    icon: <Shield size={20} />
  },
  {
    id: "billing",
    title: "Subscription",
    subtitle: "Manage billing and plans",
    icon: <CreditCard size={20} />
  },
  {
    id: "integrations",
    title: "Integrations",
    subtitle: "Connected services",
    icon: <Zap size={20} />
  },
  {
    id: "help",
    title: "Help",
    subtitle: "Documentation and support",
    icon: <HelpCircle size={20} />
  }
];

function SettingsSidebarItem(props: {
  section: SettingsSection;
  active?: boolean;
  onClick?: () => void;
}) {
  const { section, active, onClick } = props;
  return (
    <div
      className={
        "flex items-center gap-4 px-4 py-3 rounded-lg cursor-pointer transition-all duration-200 border group " +
        (active 
          ? "bg-neutral-100 border-neutral-300 hover:border-neutral-400" 
          : "bg-transparent border-transparent hover:bg-neutral-50 hover:border-neutral-200")
      }
      onClick={onClick}
    >
      <div className="h-9 w-9 rounded-lg bg-neutral-200 flex items-center justify-center text-neutral-600">
        {section.icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-neutral-900" style={{fontSize: '16px'}}>{section.title}</p>
        <p className="text-neutral-500 mt-0.5" style={{fontSize: '14px'}}>{section.subtitle}</p>
      </div>
      <ChevronRight 
        size={16} 
        className={`text-neutral-400 transition-transform ${active ? "rotate-90" : "group-hover:translate-x-1"}`} 
      />
    </div>
  );
}

function ProfileSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-neutral-900 mb-2">Profile</h2>
        <p className="text-neutral-600">Manage your personal information and avatar</p>
      </div>
      
      <div className="space-y-6">
        {/* Avatar Section */}
        <div className="flex items-start gap-6">
          <div className="h-20 w-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-xl">
            ЕА
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-neutral-900 mb-2">Profile Photo</h3>
            <p className="text-neutral-600 text-sm mb-4">Upload an image or use initials</p>
            <div className="flex gap-3">
              <button className="px-4 py-2 bg-neutral-900 text-white rounded-lg hover:opacity-90 transition-opacity">
                Upload Photo
              </button>
              <button className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors">
                Remove
              </button>
            </div>
          </div>
        </div>

        {/* Form Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">First Name</label>
            <input 
              type="text" 
              defaultValue="Egor" 
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent outline-none transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">Last Name</label>
            <input 
              type="text" 
              defaultValue="Andreev" 
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent outline-none transition-all"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-neutral-700 mb-2">Email</label>
            <input 
              type="email" 
              defaultValue="egor@example.com" 
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent outline-none transition-all"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-neutral-700 mb-2">Bio</label>
            <textarea 
              rows={3}
              placeholder="Tell us about yourself..."
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-neutral-900 focus:border-transparent outline-none transition-all resize-none"
            />
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4 border-t border-neutral-200">
          <button className="inline-flex items-center gap-2 px-6 py-3 bg-neutral-900 text-white rounded-lg hover:opacity-90 transition-opacity">
            <Save size={16} />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

function NotificationSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-neutral-900 mb-2">Уведомления</h2>
        <p className="text-neutral-600">Настройте способы получения уведомлений</p>
      </div>

      <div className="space-y-6">
        {/* Email Notifications */}
        <div className="space-y-4">
          <h3 className="font-medium text-neutral-900">Email уведомления</h3>
          <div className="space-y-3">
            {[
              { label: "Новые сообщения", description: "Получать уведомления о новых сообщениях в чате" },
              { label: "Обновления продукта", description: "Информация о новых функциях и улучшениях" },
              { label: "Маркетинговые рассылки", description: "Специальные предложения и новости" }
            ].map((item, index) => (
              <div key={index} className="flex items-start justify-between p-4 border border-neutral-200 rounded-lg">
                <div>
                  <p className="font-medium text-neutral-900">{item.label}</p>
                  <p className="text-sm text-neutral-600 mt-1">{item.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={index === 0} className="sr-only peer" />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-neutral-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neutral-900"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Push Notifications */}
        <div className="space-y-4">
          <h3 className="font-medium text-neutral-900">Push уведомления</h3>
          <div className="p-4 border border-neutral-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-neutral-900">Браузерные уведомления</p>
                <p className="text-sm text-neutral-600 mt-1">Получать уведомления прямо в браузере</p>
              </div>
              <button className="px-4 py-2 bg-neutral-900 text-white rounded-lg hover:opacity-90 transition-opacity">
                Разрешить
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PrivacySettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-neutral-900 mb-2">Приватность</h2>
        <p className="text-neutral-600">Управление настройками конфиденциальности</p>
      </div>

      <div className="space-y-6">
        <div className="space-y-4">
          <h3 className="font-medium text-neutral-900">Видимость профиля</h3>
          <div className="space-y-3">
            {[
              { label: "Публичный профиль", description: "Ваш профиль виден всем пользователям" },
              { label: "Показывать статус активности", description: "Другие видят, когда вы были в сети" },
              { label: "Индексация в поисковых системах", description: "Разрешить поисковикам индексировать профиль" }
            ].map((item, index) => (
              <div key={index} className="flex items-start justify-between p-4 border border-neutral-200 rounded-lg">
                <div>
                  <p className="font-medium text-neutral-900">{item.label}</p>
                  <p className="text-sm text-neutral-600 mt-1">{item.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={index !== 2} className="sr-only peer" />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-neutral-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neutral-900"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-medium text-neutral-900">Данные и конфиденциальность</h3>
          <div className="space-y-3">
            <button className="w-full flex items-center justify-between p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
              <div className="text-left">
                <p className="font-medium text-neutral-900">Скачать мои данные</p>
                <p className="text-sm text-neutral-600 mt-1">Получить копию всех ваших данных</p>
              </div>
              <ChevronRight size={16} className="text-neutral-400" />
            </button>
            <button className="w-full flex items-center justify-between p-4 border border-red-200 rounded-lg hover:bg-red-50 transition-colors text-red-700">
              <div className="text-left">
                <p className="font-medium">Удалить аккаунт</p>
                <p className="text-sm text-red-600 mt-1">Навсегда удалить ваш аккаунт и все данные</p>
              </div>
              <ChevronRight size={16} className="text-red-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function DefaultSettings() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-12">
      <div className="rounded-full bg-neutral-100 p-6 mb-6">
        <SettingsIcon size={48} className="text-neutral-400" />
      </div>
      <h3 className="text-2xl font-semibold text-neutral-700 mb-4">
        Настройки
      </h3>
      <p className="text-neutral-500 max-w-md text-lg">
        Выберите раздел из списка слева для настройки соответствующих параметров
      </p>
    </div>
  );
}

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState<string | null>(null);

  // Sidebar navigation links (same as in chat)
  const sidebarLinks = [
    {
      label: "Чаты",
      href: "/chat",
      icon: <div className="h-7 w-7 text-neutral-200 dark:text-neutral-200 flex-shrink-0 flex items-center justify-center">💬</div>
    },
    {
      label: "Настройки",
      href: "/settings",
      icon: <SettingsIcon className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    }
  ];

  const renderSettingsContent = () => {
    switch (activeSection) {
      case 'profile':
        return <ProfileSettings />;
      case 'notifications':
        return <NotificationSettings />;
      case 'privacy':
        return <PrivacySettings />;
      default:
        return <DefaultSettings />;
    }
  };

  return (
    <div className="h-dvh w-dvw text-neutral-900 bg-neutral-900">
      <div className="flex h-full">
        {/* Main Sidebar */}
        <Sidebar animate={true}>
          <SidebarBody className="justify-between gap-10">
            <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
              {/* Skygen Title */}
              <SidebarLink
                link={{
                  label: "Skygen",
                  href: "#",
                  icon: <Wind className="h-6 w-6 text-neutral-200 dark:text-neutral-200 flex-shrink-0" style={{ transform: "scaleX(-1)" }} />
                }}
                className="px-2 py-4 pointer-events-none"
              />
              
              {/* Отступ после названия */}
              <div className="h-6"></div>
              
              {/* Navigation Links */}
              {sidebarLinks.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
            
            {/* User Profile */}
            <div>
              <SidebarLink
                link={{
                  label: "Егор Андреевич",
                  href: "#",
                  icon: (
                    <div className="h-10 w-10 min-h-10 min-w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-base flex-shrink-0" style={{ transform: "translateX(-3px)" }}>
                      <span className="leading-none">ЕА</span>
                    </div>
                  )
                }}
              />
            </div>
          </SidebarBody>
        </Sidebar>

        {/* Settings Sidebar */}
        <aside className="w-80 border-r border-neutral-200 bg-white rounded-tl-3xl rounded-bl-3xl">
          <div className="px-4 py-6">
            <div className="mb-6">
              <h1 className="text-2xl font-semibold text-neutral-900 mb-2">Настройки</h1>
              <p className="text-neutral-600">Управление аккаунтом и предпочтениями</p>
            </div>
          </div>
          <div className="space-y-2 px-3 pb-4 overflow-y-auto">
            {settingsSections.map((section) => (
              <SettingsSidebarItem
                key={section.id}
                section={section}
                active={section.id === activeSection}
                onClick={() => setActiveSection(section.id)}
              />
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex min-w-0 flex-1 flex-col" style={{backgroundColor: '#F8F8F6'}}>
          <div className="flex-1 overflow-auto px-6 py-8">
            <div className="mx-auto max-w-4xl">
              {renderSettingsContent()}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}



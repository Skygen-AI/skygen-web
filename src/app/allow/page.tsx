"use client"

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  Check, 
  MousePointer,
  Terminal,
  Calendar,
  Monitor,
  Shield,
  Key,
  HardDrive,
  Bell,
  Settings,
  Users
} from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { AnimatedCircularProgressBar } from '@/components/ui/animated-circular-progress-bar'
import SpinnerIcon from '@/components/SpinnerIcon'
import { tauriBridge } from '@/lib/tauri-bridge'

interface PermissionStep {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  status: 'current' | 'pending' | 'ready'
  step: number
  group: string
  priority: 'critical' | 'automation' | 'user'
}

const permissionSteps: PermissionStep[] = [
  // Critical (Must Have) - 3 permissions
  {
    id: 'accessibility',
    title: 'Accessibility',
    description: 'Critical! Allows the AI agent to control cursor, clicks, keyboard input, and all UI elements.',
    icon: MousePointer,
    status: 'current',
    step: 1,
    group: 'Critical',
    priority: 'critical'
  },
  {
    id: 'screen-recording',
    title: 'Screen Recording',
    description: 'Required for analyzing screen content, taking screenshots, and understanding context.',
    icon: Monitor,
    status: 'pending',
    step: 2,
    group: 'Critical',
    priority: 'critical'
  },
  {
    id: 'full-disk',
    title: 'Full Disk Access',
    description: 'Access to all system files, including protected folders and system files.',
    icon: HardDrive,
    status: 'pending',
    step: 3,
    group: 'Critical',
    priority: 'critical'
  },
  
  // Automation - 4 permissions
  {
    id: 'automation',
    title: 'Automation',
    description: 'Enables automating system processes, managing applications, and performing complex tasks.',
    icon: Settings,
    status: 'pending',
    step: 4,
    group: 'Automation',
    priority: 'automation'
  },
  {
    id: 'terminal',
    title: 'Terminal Access',
    description: 'Execute commands in Terminal, manage the system through command line.',
    icon: Terminal,
    status: 'pending',
    step: 5,
    group: 'Automation',
    priority: 'automation'
  },
  {
    id: 'system-events',
    title: 'System Events',
    description: 'Monitor and respond to system events, automation capabilities.',
    icon: Shield,
    status: 'pending',
    step: 6,
    group: 'Automation',
    priority: 'automation'
  },
  {
    id: 'keychain',
    title: 'Keychain Access',
    description: 'Manage passwords, certificates, and other secure data.',
    icon: Key,
    status: 'pending',
    step: 7,
    group: 'Automation',
    priority: 'automation'
  },
  
  // User Features - 4 permissions
  {
    id: 'microphone',
    title: 'Microphone Access',
    description: 'Voice commands, text dictation, and audio recordings.',
    icon: Mic,
    status: 'pending',
    step: 8,
    group: 'User Features',
    priority: 'user'
  },
  {
    id: 'calendar',
    title: 'Calendar Access',
    description: 'Create events, manage schedules, and set reminders.',
    icon: Calendar,
    status: 'pending',
    step: 9,
    group: 'User Features',
    priority: 'user'
  },
  {
    id: 'contacts',
    title: 'Contacts Access',
    description: 'Access and manage contacts for communication and scheduling.',
    icon: Users,
    status: 'pending',
    step: 10,
    group: 'User Features',
    priority: 'user'
  },
  {
    id: 'notifications',
    title: 'Notifications',
    description: 'Send system notifications and receive important messages.',
    icon: Bell,
    status: 'pending',
    step: 11,
    group: 'User Features',
    priority: 'user'
  }
]

// Function to get the appropriate image for each permission
const getPermissionImage = (permissionId: string) => {
  const imageMap: { [key: string]: string } = {
    'accessibility': '/images/accessibility-demo.jpg',
    'screen-recording': '/images/recording-demo.jpg', 
    'full-disk': '/images/disk-demo.png',
    'automation': '/images/shortcuts-demo.png',
    'terminal': '/images/terminal-demo.png',
    'system-events': '/images/systemEvents-demo.avif',
    'keychain': '/images/keychain-demo.jpg',
    'microphone': '/images/audioInput-demo.png',
    'calendar': '/images/calendar-demo.png',
    'contacts': '/images/contacts-demo.webp',
    'notifications': '/images/notifications-demo.png'
  }
  return imageMap[permissionId] || '/images/audioInput-demo.png'
}

async function requestMacOSPermission(permissionId?: string): Promise<void> {
  if (!permissionId) return;
  
  try {
    console.log(`Requesting macOS permission for: ${permissionId}`);
    
    switch (permissionId) {
      case 'recording':
      case 'audioInput':
        await tauriBridge.invoke('request_screen_recording_permission');
        break;
        
      case 'accessibility':
      case 'systemEvents':
        await tauriBridge.invoke('request_accessibility_permission');
        break;
        
      case 'screenshot':
        // Trigger a screenshot to request permission
        try {
          await tauriBridge.invoke('desktop_env_screenshot');
        } catch (error) {
          console.log('Screenshot permission requested via attempt');
        }
        break;
        
      default:
        console.log(`No specific permission request for: ${permissionId}`);
        break;
    }
  } catch (error) {
    console.error(`Failed to request permission for ${permissionId}:`, error);
  }
}

export default function AllowPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [permissions, setPermissions] = useState(permissionSteps)
  const [activeGroup, setActiveGroup] = useState<'critical' | 'automation' | 'user'>('critical')
  const [isGranting, setIsGranting] = useState(false)
  const [justGranted, setJustGranted] = useState(false)
  const [grantingPermissions, setGrantingPermissions] = useState<Set<string>>(new Set())
  const [successPermissions, setSuccessPermissions] = useState<Set<string>>(new Set())

  // Check if we're past critical permissions (show 4 at once)
  const criticalPermissions = permissions.filter(p => p.priority === 'critical')
  const isPastCritical = currentStep >= criticalPermissions.length
  
  // Auto-update active group based on current step
  const currentPermission = permissions[currentStep]
  const currentPriority = currentPermission?.priority
  
  // Update active group when current step changes
  React.useEffect(() => {
    if (currentPriority === 'critical') {
      setActiveGroup('critical')
    } else if (currentPriority === 'automation') {
      setActiveGroup('automation')
    } else if (currentPriority === 'user') {
      setActiveGroup('user')
    }
    
    // Reset success state when changing steps manually
    setJustGranted(false);
    setGrantingPermissions(new Set());
    // Don't reset successPermissions - let them expire naturally
  }, [currentStep, currentPriority])

  // Check for automatic section transitions
  React.useEffect(() => {
    const currentGroupPermissions = permissions.filter(p => p.priority === activeGroup);
    const allCurrentCompleted = currentGroupPermissions.every(p => p.status === 'ready');
    
    if (allCurrentCompleted && currentGroupPermissions.length > 0) {
      const timer = setTimeout(() => {
        if (activeGroup === 'automation') {
          const firstUserIndex = permissions.findIndex(p => p.priority === 'user');
          if (firstUserIndex !== -1) {
            setCurrentStep(firstUserIndex);
          }
        }
        // If activeGroup === 'user', stay at end (all completed)
      }, 2500); // Delay to show completion
      
      return () => clearTimeout(timer);
    }
  }, [permissions, activeGroup])

  const handleGrantPermission = async () => {
    if (isGranting) return; // Prevent multiple clicks
    
    setIsGranting(true);
    
    // Request actual macOS permissions
    const currentPermission = permissions[currentStep];
    await requestMacOSPermission(currentPermission?.id);
    
    // Simulate permission granting process with delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    if (!isPastCritical) {
      // For critical permissions: handle one at a time
      setPermissions(prev => 
        prev.map((permission, index) => {
          if (index === currentStep) {
            return { ...permission, status: 'ready' as const }
          }
          return permission
        })
      )
      
      // Show success state briefly
      setJustGranted(true);
      
      // Auto-navigate to next critical permission if available
      const nextStep = currentStep + 1;
      if (nextStep < criticalPermissions.length) {
        setTimeout(() => {
          setCurrentStep(nextStep);
          setJustGranted(false); // Reset success state for next permission
        }, 1500); // Longer delay to show success state
      } else {
        // If it's the last critical permission, move to automation section
        setTimeout(() => {
          setJustGranted(false);
          const firstAutomationIndex = permissions.findIndex(p => p.priority === 'automation');
          if (firstAutomationIndex !== -1) {
            setCurrentStep(firstAutomationIndex);
          }
        }, 2000);
      }
    } else {
      // For non-critical permissions: handle batch of 4
      const remainingPermissions = permissions.slice(criticalPermissions.length)
      const startIndex = currentStep - criticalPermissions.length
      const batchSize = 4
      const batchStart = Math.floor(startIndex / batchSize) * batchSize
      const currentBatch = remainingPermissions.slice(batchStart, batchStart + batchSize)
      
      setPermissions(prev => 
        prev.map((permission, index) => {
          // Mark all permissions in current batch as ready
          const isInCurrentBatch = currentBatch.some(bp => bp.id === permission.id)
          if (isInCurrentBatch) {
            return { ...permission, status: 'ready' as const }
          }
          
          return permission
        })
      )
      
      // Show success state briefly
      setJustGranted(true);
      
      // Auto-transition to next section after delay
      setTimeout(() => {
        setJustGranted(false);
        
        // Determine next section based on current active group
        if (activeGroup === 'automation') {
          // Move to User Features
          const firstUserIndex = permissions.findIndex(p => p.priority === 'user');
          if (firstUserIndex !== -1) {
            setCurrentStep(firstUserIndex);
          }
        }
        // If activeGroup === 'user', we stay at the end (all permissions completed)
      }, 2000);
    }
    
    setIsGranting(false);
  }

  const handleIndividualGrant = async (permissionId: string) => {
    if (grantingPermissions.has(permissionId) || successPermissions.has(permissionId)) return;
    
    // Add to granting set
    setGrantingPermissions(prev => new Set(prev).add(permissionId));
    
    // Request actual macOS permissions
    await requestMacOSPermission(permissionId);
    
    // Simulate permission granting process
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Update permission status
    setPermissions(prev => 
      prev.map(p => 
        p.id === permissionId 
          ? { ...p, status: 'ready' as const }
          : p
      )
    );
    
    // Remove from granting, add to success
    setGrantingPermissions(prev => {
      const newSet = new Set(prev);
      newSet.delete(permissionId);
      return newSet;
    });
    
    setSuccessPermissions(prev => new Set(prev).add(permissionId));
    
    // Keep success state permanently - don't reset it
    
    // Automatic section transition is now handled by useEffect
  }

  const isLastStep = currentStep === permissions.length - 1
  const allCompleted = permissions.every(p => p.status === 'ready')
  const criticalCompleted = criticalPermissions.every(p => p.status === 'ready')
  
  // Get current permissions to display (1 for critical, 4 for others)
  const getCurrentPermissions = () => {
    if (!isPastCritical) {
      return [currentPermission]
    }
    
    // Show 4 permissions starting from current step
    const remainingPermissions = permissions.slice(criticalPermissions.length)
    const startIndex = currentStep - criticalPermissions.length
    const batchSize = 4
    const batchStart = Math.floor(startIndex / batchSize) * batchSize
    
    return remainingPermissions.slice(batchStart, batchStart + batchSize)
  }
  
  const currentPermissions = getCurrentPermissions()
  
  // Get permissions for active group
  const getActiveGroupPermissions = () => {
    return permissions.filter(p => p.priority === activeGroup)
  }
  
  const activeGroupPermissions = getActiveGroupPermissions()
  
  // Calculate progress for each group
  const getGroupProgress = (groupPriority: 'critical' | 'automation' | 'user') => {
    const groupPermissions = permissions.filter(p => p.priority === groupPriority)
    const completedPermissions = groupPermissions.filter(p => p.status === 'ready')
    return Math.round((completedPermissions.length / groupPermissions.length) * 100)
  }

  return (
    <div className="h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="w-full max-w-7xl bg-white rounded-2xl shadow-xl overflow-hidden flex h-[800px]">
        {/* Left side - Step content */}
        <div className="flex-1 flex flex-col px-8 py-12">
          {!isPastCritical ? (
            // Single permission layout for critical
            <div className="max-w-md mx-auto flex flex-col h-full">
              {/* Permission icon and title at top */}
              <AnimatePresence mode="wait">
    <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
                  className="flex items-center gap-4 mb-8"
    >
                  <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center">
                    <currentPermission.icon className="w-8 h-8 text-blue-600" />
        </div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    {currentPermission.title}
                  </h1>
                </motion.div>
              </AnimatePresence>

              {/* Mock Photo in the middle */}
              <div className="flex-1 flex items-center justify-center">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.3 }}
                    className="w-[648px] h-[432px] rounded-xl overflow-hidden shadow-lg"
                  >
                    <img
                      src={getPermissionImage(currentPermission.id)}
                      alt={`${currentPermission.title} Demo`}
                      className="w-full h-full object-cover"
                    />
                  </motion.div>
                </AnimatePresence>
        </div>
        
              {/* Description and buttons at bottom */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="text-base text-gray-600 mb-6 leading-relaxed">
                    {currentPermission.description}
                  </p>

            <Button
                    onClick={handleGrantPermission}
                    size="lg"
                    className={`px-6 py-3 text-base rounded-lg w-full transition-all duration-300 ${
                      justGranted 
                        ? 'bg-green-600 opacity-70' 
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                    disabled={isGranting || justGranted}
                  >
                    {justGranted ? (
                      <div className="flex items-center gap-2">
                        <Check className="w-5 h-5" />
                        Permission Granted!
                      </div>
                    ) : isGranting ? (
                      <div className="flex items-center gap-2">
                        <SpinnerIcon className="w-5 h-5 animate-spin" />
                        Granting Permission...
                      </div>
                    ) : criticalCompleted && !isPastCritical ? (
                      'Critical Permissions Complete'
                    ) : allCompleted ? (
                      'All Permissions Granted'
                    ) : (
                      'Grant Permission'
                    )}
            </Button>
            
                </motion.div>
              </AnimatePresence>
            </div>
          ) : (
            // Grid layout for 4 permissions
            <div className="h-full">
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${currentStep}-grid`}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <div className="flex items-center justify-center gap-4 mb-8">
                    <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                      {currentPermissions[0]?.priority === 'automation' ? (
                        <Settings className="w-6 h-6 text-blue-600" />
                      ) : (
                        <Users className="w-6 h-6 text-green-600" />
                      )}
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900">
                      {currentPermissions[0]?.group || 'Additional Permissions'}
                    </h1>
                  </div>
                  
                  {/* 2x2 Grid of permission cards */}
                  <div className="grid grid-cols-2 gap-6 h-[calc(100%-4rem)]">
                    {currentPermissions.map((permission, index) => (
                      <div key={permission.id} className="flex flex-col bg-gray-50 rounded-xl p-4">
                        {/* Header */}
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
                            <permission.icon className="w-6 h-6 text-blue-600" />
                          </div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {permission.title}
                          </h3>
          </div>
                        
                        {/* Photo */}
                        <div className="flex-1 flex items-center justify-center mb-4">
                                                    <div className="w-full h-24 rounded-lg overflow-hidden shadow-sm">
                            <img
                              src={getPermissionImage(permission.id)}
                              alt={`${permission.title} Demo`}
                              className="w-full h-full object-cover"
                            />
        </div>
      </div>
                        
                        {/* Description */}
                        <p className="text-sm text-gray-600 mb-4 leading-relaxed flex-1">
                          {permission.description}
                        </p>
                        
                        {/* Individual button for each permission */}
                        <Button
                          onClick={() => handleIndividualGrant(permission.id)}
                          size="sm"
                          className={`text-sm rounded-lg w-full transition-all duration-300 ${
                            successPermissions.has(permission.id)
                              ? 'bg-green-600 opacity-70'
                              : 'bg-blue-600 hover:bg-blue-700'
                          }`}
                          disabled={grantingPermissions.has(permission.id) || successPermissions.has(permission.id)}
                        >
                          {successPermissions.has(permission.id) ? (
                            <div className="flex items-center gap-1">
                              <Check className="w-4 h-4" />
                              Granted!
                            </div>
                          ) : grantingPermissions.has(permission.id) ? (
                            <div className="flex items-center gap-1">
                              <SpinnerIcon className="w-4 h-4 animate-spin" />
                              Granting...
                            </div>
                          ) : (
                            'Grant'
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                  

                </motion.div>
              </AnimatePresence>
            </div>
          )}
        </div>

                {/* Right side - Permission groups */}
        <div className="w-80 bg-white border-l border-gray-200 p-8 flex flex-col">
          <h2 className="text-xl font-bold text-gray-900 mb-8">Permission Groups</h2>
          
          <div className="flex-1 flex flex-col justify-center relative">
            
            {/* Critical */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="group relative z-10"
            >
              <div 
                className="flex items-center gap-6 py-6 cursor-pointer"
                onClick={() => {
                  // Navigate to first critical permission
                  const firstCriticalIndex = permissions.findIndex(p => p.priority === 'critical')
                  if (firstCriticalIndex !== -1) {
                    setCurrentStep(firstCriticalIndex)
                    setActiveGroup('critical')
                  }
                }}
              >
                <div className="relative z-10">
                  <AnimatedCircularProgressBar
                    value={getGroupProgress('critical')}
                    max={100}
                    min={0}
                    gaugePrimaryColor={activeGroup === 'critical' ? '#3b82f6' : '#6b7280'}
                    gaugeSecondaryColor="#e5e7eb"
                    className={`size-8 text-xs transition-all duration-300 ${
                      activeGroup === 'critical' ? 'scale-110' : ''
                    } group-hover:scale-110`}
                  />
                </div>
                <h3 className="text-2xl font-bold text-gray-700 group-hover:text-gray-900 transition-all duration-300 group-hover:translate-x-2">
                  Critical
                </h3>
              </div>
              
              {/* Critical Permissions Accordion */}
              <AnimatePresence>
                {activeGroup === 'critical' && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-2 pb-4">
                      {permissions.filter(p => p.priority === 'critical').map((permission, index) => (
                        <div
                          key={permission.id}
                          className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-200 ${
                            permission.status === 'ready' 
                              ? 'bg-green-50 border-green-200' 
                              : currentPermission && currentPermission.id === permission.id
                                ? 'bg-blue-50 border-blue-200'
                                : 'bg-gray-50 hover:bg-gray-100'
                          } border`}
                        >
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                            permission.status === 'ready'
                              ? 'bg-green-500 text-white'
                              : currentPermission && currentPermission.id === permission.id
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-300 text-gray-600'
                          }`}>
                            {permission.status === 'ready' ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              permission.step
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium truncate ${
                              permission.status === 'ready' 
                                ? 'text-green-700'
                                : currentPermission && currentPermission.id === permission.id
                                  ? 'text-blue-700'
                                  : 'text-gray-700'
                            }`}>
                              {permission.title}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Automation */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="group relative z-10"
            >
              <div 
                className="flex items-center gap-6 py-6 cursor-pointer"
                onClick={() => {
                  // Navigate to first automation permission
                  const firstAutomationIndex = permissions.findIndex(p => p.priority === 'automation')
                  if (firstAutomationIndex !== -1) {
                    setCurrentStep(firstAutomationIndex)
                    setActiveGroup('automation')
                  }
                }}
              >
                <div className="relative z-10">
                  <AnimatedCircularProgressBar
                    value={getGroupProgress('automation')}
                    max={100}
                    min={0}
                    gaugePrimaryColor={activeGroup === 'automation' ? '#3b82f6' : '#6b7280'}
                    gaugeSecondaryColor="#e5e7eb"
                    className={`size-8 text-xs transition-all duration-300 ${
                      activeGroup === 'automation' ? 'scale-110' : ''
                    } group-hover:scale-110`}
                  />
                </div>
                <h3 className="text-2xl font-bold text-gray-700 group-hover:text-gray-900 transition-all duration-300 group-hover:translate-x-2">
                  Automation
                </h3>
              </div>
              
              {/* Automation Permissions Accordion */}
              <AnimatePresence>
                {activeGroup === 'automation' && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-2 pb-4">
                      {permissions.filter(p => p.priority === 'automation').map((permission, index) => (
                        <div
                          key={permission.id}
                          className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-200 ${
                            permission.status === 'ready' 
                              ? 'bg-green-50 border-green-200' 
                              : currentPermission && currentPermission.id === permission.id
                                ? 'bg-blue-50 border-blue-200'
                                : 'bg-gray-50 hover:bg-gray-100'
                          } border`}
                        >
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                            permission.status === 'ready'
                              ? 'bg-green-500 text-white'
                              : currentPermission && currentPermission.id === permission.id
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-300 text-gray-600'
                          }`}>
                            {permission.status === 'ready' ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              permission.step
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium truncate ${
                              permission.status === 'ready' 
                                ? 'text-green-700'
                                : currentPermission && currentPermission.id === permission.id
                                  ? 'text-blue-700'
                                  : 'text-gray-700'
                            }`}>
                              {permission.title}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* User Features */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="group relative z-10"
            >
              <div 
                className="flex items-center gap-6 py-6 cursor-pointer"
                onClick={() => {
                  // Navigate to first user permission
                  const firstUserIndex = permissions.findIndex(p => p.priority === 'user')
                  if (firstUserIndex !== -1) {
                    setCurrentStep(firstUserIndex)
                    setActiveGroup('user')
                  }
                }}
              >
                <div className="relative z-10">
                  <AnimatedCircularProgressBar
                    value={getGroupProgress('user')}
                    max={100}
                    min={0}
                    gaugePrimaryColor={activeGroup === 'user' ? '#3b82f6' : '#6b7280'}
                    gaugeSecondaryColor="#e5e7eb"
                    className={`size-8 text-xs transition-all duration-300 ${
                      activeGroup === 'user' ? 'scale-110' : ''
                    } group-hover:scale-110`}
                  />
                </div>
                <h3 className="text-2xl font-bold text-gray-700 group-hover:text-gray-900 transition-all duration-300 group-hover:translate-x-2">
                  User Features
                </h3>
              </div>
              
              {/* User Features Permissions Accordion */}
              <AnimatePresence>
                {activeGroup === 'user' && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-2 pb-4">
                      {permissions.filter(p => p.priority === 'user').map((permission, index) => (
                        <div
                          key={permission.id}
                          className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-200 ${
                            permission.status === 'ready' 
                              ? 'bg-green-50 border-green-200' 
                              : currentPermission && currentPermission.id === permission.id
                                ? 'bg-blue-50 border-blue-200'
                                : 'bg-gray-50 hover:bg-gray-100'
                          } border`}
                        >
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                            permission.status === 'ready'
                              ? 'bg-green-500 text-white'
                              : currentPermission && currentPermission.id === permission.id
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-300 text-gray-600'
                          }`}>
                            {permission.status === 'ready' ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              permission.step
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium truncate ${
                              permission.status === 'ready' 
                                ? 'text-green-700'
                                : currentPermission && currentPermission.id === permission.id
                                  ? 'text-blue-700'
                                  : 'text-gray-700'
                            }`}>
                              {permission.title}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
          
          {/* Continue button at bottom */}
          {criticalCompleted && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="mt-auto pt-8"
            >
              <Button
                asChild
                size="lg"
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 text-base rounded-lg w-full"
              >
                <Link href="/app">
                  Continue
                </Link>
              </Button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

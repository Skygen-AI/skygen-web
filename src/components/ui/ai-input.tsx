"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Image from "next/image"
import { AnimatePresence, motion } from "framer-motion"
import { Bot, Paperclip, Plus, Send, Monitor, Smartphone, Laptop, Tablet, HardDrive, Play, Mic } from "lucide-react"

import { cn } from "@/lib/utils"
import { Textarea } from "@/components/ui/textarea"
import { GradientText } from "@/components/ui/gradient-text"

interface UseAutoResizeTextareaProps {
  minHeight: number
  maxHeight?: number
}

function useAutoResizeTextarea({
  minHeight,
  maxHeight,
}: UseAutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current
      if (!textarea) return

      if (reset) {
        textarea.style.height = `${minHeight}px`
        return
      }

      // Временно отключаем transition для точного измерения
      const originalTransition = textarea.style.transition
      textarea.style.transition = 'none'
      
      // Сбрасываем высоту до auto для получения правильного scrollHeight
      textarea.style.height = 'auto'
      
      // Вычисляем новую высоту на основе содержимого
      const scrollHeight = textarea.scrollHeight
      const newHeight = Math.max(
        minHeight,
        Math.min(scrollHeight, maxHeight ?? Number.POSITIVE_INFINITY)
      )

      // Возвращаем transition и устанавливаем новую высоту
      textarea.style.transition = originalTransition
      textarea.style.height = `${newHeight}px`
    },
    [minHeight, maxHeight]
  )

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = `${minHeight}px`
    }
  }, [minHeight])

  useEffect(() => {
    const handleResize = () => adjustHeight()
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [adjustHeight])

  return { textareaRef, adjustHeight }
}

const MIN_HEIGHT = 44  // Высота для одной строки (примерно 24px текст + 20px padding)
const MAX_HEIGHT = 140 // Высота для 5 строк (примерно 120px текст + 20px padding)

const AnimatedPlaceholder = ({ showAgent }: { showAgent: boolean }) => (
  <AnimatePresence mode="wait">
    <motion.p
      key={showAgent ? "agent" : "ask"}
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -5 }}
      transition={{ duration: 0.1 }}
      className="pointer-events-none w-[200px] text-xl absolute text-black/70 dark:text-neutral-300"
    >
{showAgent ? "Use Skygen Agent..." : "Ask Skygen..."}
    </motion.p>
  </AnimatePresence>
)

interface AiInputProps {
  onSendMessage?: (message: string) => void;
}

export function AiInput({ onSendMessage }: AiInputProps) {
  const [value, setValue] = useState("")
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: MIN_HEIGHT,
    maxHeight: MAX_HEIGHT,
  })
  const [showAgent, setShowAgent] = useState(true)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isClient, setIsClient] = useState(false)
  const [waveHeights, setWaveHeights] = useState<number[]>(Array(12).fill(20))
  const [recordingTime, setRecordingTime] = useState(0)
  
  // Определение типа устройства
  const [deviceType, setDeviceType] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  
  const deviceSections = {
    sandbox: [
      { name: "Run in Sandbox", icon: Play, status: "sandbox" }
    ],
    online: [
      { name: "Mac", icon: Monitor, status: "online" },
      { name: "iPhone", icon: Smartphone, status: "online" },
      { name: "Windows", icon: Laptop, status: "online" }
    ],
    offline: [
      { name: "iPad", icon: Tablet, status: "offline" },
      { name: "Android Phone", icon: Smartphone, status: "offline" },
      { name: "Android Tablet", icon: Tablet, status: "offline" },
      { name: "Linux", icon: Monitor, status: "offline" },
      { name: "Desktop", icon: HardDrive, status: "offline" }
    ]
  }

  // Функция для получения иконки устройства по имени
  const getDeviceIcon = (deviceName: string) => {
    const allDevices = [
      ...deviceSections.sandbox,
      ...deviceSections.online,
      ...deviceSections.offline
    ]
    const device = allDevices.find(d => d.name === deviceName)
    return device ? device.icon : Monitor // По умолчанию Monitor
  }
  
  useEffect(() => {
    const getDeviceType = () => {
      const userAgent = navigator.userAgent.toLowerCase()
      if (/ipad/.test(userAgent)) return "iPad"
      if (/iphone/.test(userAgent)) return "iPhone"
      if (/android.*mobile/.test(userAgent)) return "Android Phone"
      if (/android/.test(userAgent)) return "Android Tablet"
      if (/macintosh/.test(userAgent)) return "Mac"
      if (/windows/.test(userAgent)) return "Windows"
      if (/linux/.test(userAgent)) return "Linux"
      return "Desktop"
    }
    
    setDeviceType(getDeviceType())
  }, [])
  
  // Закрытие дропдауна при клике вне его
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.device-dropdown')) {
        setIsDropdownOpen(false)
      }
    }
    
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isDropdownOpen])

  const handelClose = (e: any) => {
    e.preventDefault()
    e.stopPropagation()
    if (fileInputRef.current) {
      fileInputRef.current.value = "" // Reset file input
    }
    setImagePreview(null) // Use null instead of empty string
  }

  const handelChange = (e: any) => {
    const file = e.target.files ? e.target.files[0] : null
    if (file) {
      setImagePreview(URL.createObjectURL(file))
    }
  }

  const handleSubmit = () => {
    if (value.trim() && onSendMessage) {
      onSendMessage(value.trim());
    }
    setValue("")
    adjustHeight(true)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const handleVoiceStart = () => {
    setIsRecording(true)
    setRecordingTime(0)
    console.log("Voice recording started")
  }

  const handleVoiceStop = (duration: number) => {
    setIsRecording(false)
    setWaveHeights(Array(12).fill(20)) // Сбрасываем высоты волн
    setRecordingTime(0) // Сбрасываем таймер
    console.log("Voice recording stopped, duration:", duration)
    // Здесь можно добавить логику обработки аудио
  }

  // Автоматически подстраиваем высоту при изменении значения
  useEffect(() => {
    adjustHeight()
  }, [value, adjustHeight])

  // Устанавливаем флаг клиентской стороны
  useEffect(() => {
    setIsClient(true)
  }, [])

  // Анимация волн во время записи
  useEffect(() => {
    if (!isRecording) return

    const interval = setInterval(() => {
      setWaveHeights(prev => 
        prev.map(() => 20 + Math.random() * 80)
      )
    }, 400) // Обновляем каждые 400ms для плавной анимации

    return () => clearInterval(interval)
  }, [isRecording])

  // Таймер записи
  useEffect(() => {
    if (!isRecording) return

    const timer = setInterval(() => {
      setRecordingTime(prev => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [isRecording])

  useEffect(() => {
    return () => {
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview)
      }
    }
  }, [imagePreview])
  return (
    <div className="w-full py-2">
      <div className="relative w-full rounded-xl bg-white border border-neutral-200 flex flex-col p-2 dark:bg-neutral-800 dark:border-neutral-700">
          <div className="relative">
              <Textarea
                id="ai-input-04"
                value={value}
                placeholder=""
                className="w-full px-3 py-2 bg-transparent border-none text-black resize-none focus-visible:ring-0 focus:outline-none focus:ring-0 focus:border-none focus:rounded-none leading-[1.4] text-xl overflow-y-auto transition-[height] duration-300 ease-out active:scale-100 dark:text-neutral-200"
                style={{ minHeight: `${MIN_HEIGHT}px`, maxHeight: `${MAX_HEIGHT}px` }}
                ref={textareaRef}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleSubmit()
                  }
                }}
                onChange={(e) => {
                  setValue(e.target.value)
                  // adjustHeight будет вызван через useEffect
                }}
              />
              {!value && (
                <div className="absolute left-3 top-2">
                  <AnimatedPlaceholder showAgent={showAgent} />
                </div>
              )}
          </div>

          <div className="h-14 bg-transparent">
            <div className="absolute left-3 bottom-1.5 flex items-center gap-2">
              <label
                className={cn(
                  "cursor-pointer relative rounded-full p-3 bg-neutral-100 dark:bg-neutral-700",
                  imagePreview
                    ? "bg-[#ff3f17]/15 border border-[#ff3f17] text-[#ff3f17] dark:bg-[#ff3f17]/20"
                    : "bg-neutral-100 text-neutral-600 hover:text-black dark:bg-neutral-700 dark:text-white dark:hover:text-white"
                )}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handelChange}
                  className="hidden"
                />
                <Paperclip
                  className={cn(
                    "w-5 h-5 text-neutral-600 hover:text-black transition-colors dark:text-white dark:hover:text-white",
                    imagePreview && "text-[#ff3f17]"
                  )}
                />
                {imagePreview && (
                  <div className="absolute w-[100px] h-[100px] top-14 -left-4">
                    <Image
                      className="object-cover rounded-2xl"
                      src={imagePreview || "/picture1.jpeg"}
                      height={500}
                      width={500}
                      alt="additional image"
                    />
                    <button
                      onClick={handelClose}
                      className="bg-[#e8e8e8] text-[#464646] absolute -top-1 -left-1 shadow-3xl rounded-full rotate-45"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </label>
              <button
                type="button"
                onClick={() => {
                  setShowAgent(!showAgent)
                }}
                className={cn(
                  "rounded-full transition-all flex items-center gap-2 px-2 py-1.5 h-10",
                  showAgent
                    ? "agent-gradient-border border-transparent"
                    : "bg-neutral-100 border-transparent text-neutral-600 hover:text-black dark:bg-neutral-700 dark:text-white dark:hover:text-white"
                )}
              >
                <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                  <motion.div
                    animate={{
                      rotate: showAgent ? 360 : 0,
                      scale: showAgent ? 1.1 : 1,
                    }}
                    whileHover={{
                      rotate: showAgent ? 360 : 15,
                      scale: 1.1,
                      transition: {
                        type: "spring",
                        stiffness: 300,
                        damping: 10,
                      },
                    }}
                    transition={{
                      type: "spring",
                      stiffness: 260,
                      damping: 25,
                    }}
                  >
                    <Bot
                      className={cn(
                        "w-5 h-5",
                        showAgent ? "" : "text-inherit"
                      )}
                    />
                  </motion.div>
                </div>
                <AnimatePresence>
                  {showAgent && (
                    <motion.span
                      initial={{ width: 0, opacity: 0 }}
                      animate={{
                        width: "auto",
                        opacity: 1,
                      }}
                      exit={{ width: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-base overflow-hidden whitespace-nowrap flex-shrink-0"
                    >
                      Agent
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
              
              {/* Кастомный дропдаун с типом устройства */}
              <AnimatePresence>
                {showAgent && deviceType && (
                  <motion.div
                    initial={{ width: 0, opacity: 0, x: -10 }}
                    animate={{
                      width: "auto",
                      opacity: 1,
                      x: -12,
                    }}
                    exit={{ width: 0, opacity: 0, x: -10 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="ml-3 relative device-dropdown"
                  >
                    {/* Кнопка дропдауна */}
                    <button
                      onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-neutral-700 dark:hover:bg-neutral-600 dark:text-neutral-300 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors flex items-center gap-2"
                    >
                      {(() => {
                        const DeviceIcon = getDeviceIcon(deviceType)
                        return <DeviceIcon className="w-4 h-4 text-slate-600 dark:text-neutral-300" />
                      })()}
                      {deviceType}
                      <motion.div
                        animate={{ rotate: isDropdownOpen ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                          <path d="M3 5l3 3 3-3H3z"/>
                        </svg>
                      </motion.div>
                    </button>
                    
                    {/* Выпадающее меню */}
                    <AnimatePresence>
                      {isDropdownOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: 10, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: 10, scale: 0.95 }}
                          transition={{ duration: 0.2 }}
                          className="absolute bottom-full mb-2 left-0 bg-white border border-slate-200 rounded-xl shadow-lg py-1 min-w-[200px] max-h-[300px] overflow-y-auto dark:bg-neutral-800 dark:border-neutral-700"
                          style={{ 
                            zIndex: 9999,
                            position: 'absolute',
                            bottom: '100%',
                            left: '0',
                            marginBottom: '8px'
                          }}
                        >
                          {/* Sandbox секция */}
                          <div className="px-3 py-2 text-xs font-semibold text-blue-600 uppercase tracking-wide border-b border-slate-100 dark:border-neutral-700 dark:text-blue-400">
                            Sandbox
                          </div>
                          {deviceSections.sandbox.map((device) => (
                            <button
                              key={device.name}
                              onClick={() => {
                                setDeviceType(device.name)
                                setIsDropdownOpen(false)
                              }}
                              className={cn(
                                "w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-blue-50 transition-all duration-150 border-none cursor-pointer flex items-center gap-3 dark:text-white dark:hover:bg-neutral-700",
                                deviceType === device.name ? "bg-blue-100 text-blue-900 font-medium dark:bg-blue-900 dark:text-white" : ""
                              )}
                            >
                              <device.icon 
                                className={cn(
                                  "w-4 h-4 transition-colors",
                                  device.status === "sandbox" ? "text-blue-500" : "text-slate-600 dark:text-neutral-300"
                                )} 
                              />
                              <span>{device.name}</span>
                            </button>
                          ))}
                          
                          {/* Divider */}
                          <div className="h-px bg-slate-200 mx-2 my-1 dark:bg-neutral-700"></div>

                          {/* Online секция */}
                          <div className="px-3 py-2 text-xs font-semibold text-green-600 uppercase tracking-wide border-b border-slate-100 dark:border-neutral-700 dark:text-green-400">
                            Online
                          </div>
                          {deviceSections.online.map((device) => (
                            <button
                              key={device.name}
                              onClick={() => {
                                setDeviceType(device.name)
                                setIsDropdownOpen(false)
                              }}
                              className={cn(
                                "w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-all duration-150 border-none cursor-pointer flex items-center gap-3 dark:text-white dark:hover:bg-neutral-700",
                                deviceType === device.name ? "bg-slate-100 text-slate-900 font-medium dark:bg-neutral-700 dark:text-white" : ""
                              )}
                            >
                              <device.icon 
                                className={cn(
                                  "w-4 h-4 transition-colors",
                                  device.status === "online" ? "text-green-500" : "text-slate-600 dark:text-neutral-300"
                                )} 
                              />
                              <span>{device.name}</span>
                            </button>
                          ))}
                          
                          {/* Divider */}
                          <div className="h-px bg-slate-200 mx-2 my-1"></div>
                          
                          {/* Offline секция */}
                          <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wide border-b border-slate-100">
                            Offline
                          </div>
                          {deviceSections.offline.map((device) => (
                            <button
                              key={device.name}
                              onClick={() => {
                                setDeviceType(device.name)
                                setIsDropdownOpen(false)
                              }}
                              className={cn(
                                "w-full text-left px-3 py-2 text-sm text-slate-500 hover:bg-slate-50 transition-all duration-150 border-none cursor-pointer flex items-center gap-3",
                                deviceType === device.name ? "bg-slate-100 text-slate-700 font-medium" : ""
                              )}
                            >
                              <device.icon 
                                className={cn(
                                  "w-4 h-4 transition-colors opacity-60",
                                  device.status === "offline" ? "text-slate-400" : "text-slate-600"
                                )} 
                              />
                              <span>{device.name}</span>
                            </button>
                          ))}
                          
                          {Object.values(deviceSections).every(section => section.length === 0) && (
                            <div className="px-4 py-3 text-sm text-slate-500">
                              Устройства не найдены
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <div className="absolute right-3 bottom-1.5 flex items-center gap-1">
              {/* Audio wave visualization with timer */}
              <AnimatePresence>
                {isRecording && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8, x: 20 }}
                    animate={{ opacity: 1, scale: 1, x: 0 }}
                    exit={{ opacity: 0, scale: 0.8, x: 20 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="bg-neutral-100 rounded-full flex items-center mr-1 h-10"
                  >
                    {/* Timer */}
                    <span className="text-xs font-mono text-neutral-600 px-2">
                      {formatTime(recordingTime)}
                    </span>
                    
                    {/* Wave */}
                    <div className="h-8 w-24 flex items-center justify-center gap-0.5 pr-2">
                      {waveHeights.map((height, i) => (
                        <div
                          key={i}
                          className={cn(
                            "w-0.5 rounded-full transition-all duration-300 bg-red-500/60"
                          )}
                          style={{
                            height: `${height}%`,
                          }}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              
              <button
                type="button"
                onClick={() => {
                  if (isRecording) {
                    handleVoiceStop(0)
                  } else {
                    handleVoiceStart()
                  }
                }}
                className={cn(
                  "rounded-full p-3 transition-all duration-300",
                  isRecording
                    ? "bg-red-500/15 text-red-500"
                    : "bg-neutral-100 text-neutral-600 hover:text-black dark:bg-neutral-700 dark:text-white dark:hover:text-white"
                )}
              >
                <AnimatePresence mode="wait">
                  {isRecording ? (
                    <motion.div
                      key="recording"
                      animate={{
                        rotate: 360,
                        scale: 1.1,
                      }}
                      whileHover={{
                        rotate: 360,
                        scale: 1.1,
                        transition: {
                          type: "spring",
                          stiffness: 300,
                          damping: 10,
                        },
                      }}
                      transition={{
                        type: "spring",
                        stiffness: 260,
                        damping: 25,
                      }}
                      className="w-5 h-5 rounded-sm bg-red-500 animate-pulse"
                    />
                  ) : (
                    <motion.div
                      key="microphone"
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.5 }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                    >
                      <Mic className="w-5 h-5" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                className={cn(
                  "rounded-full p-3 transition-colors",
                  value
                    ? "bg-[#ff3f17]/15 text-[#ff3f17]"
                    : "bg-neutral-100 text-neutral-600 hover:text-black dark:bg-neutral-700 dark:text-white dark:hover:text-white"
                )}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
      </div>
    </div>
  )
}

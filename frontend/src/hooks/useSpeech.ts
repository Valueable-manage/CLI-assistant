/**
 * 语音输入/输出 Hook
 *
 * useVoiceInput  - 调麦克风识别语音 → 返回文字
 * useTTS         - 文字转语音播放（浏览器内置 TTS）
 *
 * 均依赖浏览器原生 Web Speech API，Chrome / Edge 支持，Firefox 不支持语音识别。
 */
import { useState, useRef, useCallback, useEffect } from "react";

// ── TypeScript 类型补充（Web Speech API 不在标准 lib 里）──
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}
interface SpeechRecognitionResultList {
  length: number;
  [index: number]: SpeechRecognitionResult;
}
interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
}
interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
interface SpeechRecognition extends EventTarget {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((e: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

// ════════════════════════════════════════════════════════
//  语音输入
// ════════════════════════════════════════════════════════

export interface VoiceInputState {
  listening: boolean;       // 是否正在录音
  supported: boolean;       // 浏览器是否支持
  transcript: string;       // 最新识别结果（实时）
  start: () => void;
  stop: () => void;
}

/**
 * 封装 SpeechRecognition API。
 * @param onResult 识别完成回调，传入最终文字
 */
export function useVoiceInput(onResult: (text: string) => void): VoiceInputState {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // 检查浏览器支持
  const supported =
    typeof window !== "undefined" &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition);

  const start = useCallback(() => {
    if (!supported || listening) return;

    const Ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    const rec: SpeechRecognition = new Ctor();
    rec.lang = "zh-CN";        // 中文识别
    rec.interimResults = true; // 边说边显示（中间结果）
    rec.continuous = true;     // 持续识别，直到手动点击停止

    rec.onresult = (e: SpeechRecognitionEvent) => {
      let interim = "";
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) final += t;
        else interim += t;
      }
      // 实时展示中间结果
      setTranscript(final || interim);
      // 有最终结果时回调
      if (final) onResult(final);
    };

    rec.onerror = () => {
      setListening(false);
      setTranscript("");
    };

    rec.onend = () => {
      setListening(false);
    };

    rec.start();
    recognitionRef.current = rec;
    setListening(true);
    setTranscript("");
  }, [supported, listening, onResult]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
  }, []);

  // 组件卸载时停止识别
  useEffect(() => () => { recognitionRef.current?.stop(); }, []);

  return { listening, supported, transcript, start, stop };
}


// ════════════════════════════════════════════════════════
//  语音输出（TTS）
// ════════════════════════════════════════════════════════

export interface TTSState {
  speaking: boolean;    // 是否正在朗读
  supported: boolean;
  speak: (text: string) => void;
  cancel: () => void;
}

/** 过滤掉 Markdown 符号，避免朗读出 **粗体** ### 标题 等标记 */
function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, "")   // 代码块
    .replace(/`[^`]+`/g, "")          // 行内代码
    .replace(/#{1,6}\s/g, "")         // 标题符号
    .replace(/[*_~>|]/g, "")          // 强调/引用/表格
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // 链接
    .replace(/\n{2,}/g, "。")         // 段落换行 → 停顿
    .trim();
}

/** 封装 SpeechSynthesis API */
export function useTTS(): TTSState {
  const [speaking, setSpeaking] = useState(false);
  const supported =
    typeof window !== "undefined" && "speechSynthesis" in window;

  const speak = useCallback((text: string) => {
    if (!supported) return;
    // 取消上一条（防止叠播）
    window.speechSynthesis.cancel();

    const cleaned = stripMarkdown(text);
    if (!cleaned) return;

    const utter = new SpeechSynthesisUtterance(cleaned);
    utter.lang = "zh-CN";
    utter.rate = 1.1;  // 略快，听起来更自然

    // 优先选中文语音（如果系统有的话）
    const voices = window.speechSynthesis.getVoices();
    const zhVoice = voices.find((v) => v.lang.startsWith("zh"));
    if (zhVoice) utter.voice = zhVoice;

    utter.onstart = () => setSpeaking(true);
    utter.onend   = () => setSpeaking(false);
    utter.onerror = () => setSpeaking(false);

    window.speechSynthesis.speak(utter);
  }, [supported]);

  const cancel = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [supported]);

  // 组件卸载时停止朗读
  useEffect(() => () => { window.speechSynthesis?.cancel(); }, []);

  return { speaking, supported, speak, cancel };
}

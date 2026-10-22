import os

f = 'core/src/components/ui/TerminalMockup.vue'
lines = open(f).readlines()
lines[193] = "  <span class=\"text-[#27C93F] font-bold mr-2\">root@server<span class=\"text-white\">:</span><span class=\"text-[#3A96DD]\">~/app</span><span class=\"text-white\">#</span></span><span class=\"text-[#E5E5E5]\" v-html=\"step.highlightedCmd\"></span><span v-if=\"step.isTyping\" :style=\"{ opacity: (relativeTime % 1000) < 500 ? 1 : 0 }\" class=\"bg-[#8E8E93] inline-block align-middle ml-1\" :class=\"mobile ? 'w-[6px] h-[12px]' : 'w-[8px] h-[15px]'\"></span>\n"
lines[200] = "  <span class=\"text-[#27C93F] font-bold mr-2\">root@server<span class=\"text-white\">:</span><span class=\"text-[#3A96DD]\">~/app</span><span class=\"text-white\">#</span></span><span :style=\"{ opacity: (relativeTime % 1000) < 500 ? 1 : 0 }\" class=\"bg-[#8E8E93] inline-block align-middle\" :class=\"mobile ? 'w-[6px] h-[12px]' : 'w-[8px] h-[15px]'\"></span>\n"
open(f, 'w').writelines(lines)
print("Fixed TerminalMockup.vue")

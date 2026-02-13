#!/usr/bin/env python3
# 终端交互工具模块

import sys
import time
from enum import Enum
from typing import Dict, List, Any
import ctypes

# 启用 Windows 终端的 ANSI 颜色支持
if sys.platform == "win32":
    # 启用 ANSI 转义序列支持
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


class Color(Enum):
    """终端颜色枚举 - 创新配色方案"""

    # 重置
    RESET = "\033[0m"

    # 基础前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 亮色调前景色（创新配色）
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 创新主题色
    ORANGE = "\033[38;5;208m"  # 橙色
    PINK = "\033[38;5;219m"  # 粉色
    PURPLE = "\033[38;5;129m"  # 紫色
    TEAL = "\033[38;5;30m"  # 青绿色
    LIME = "\033[38;5;154m"  # 酸橙绿
    INDIGO = "\033[38;5;61m"  # 靛蓝色
    VIOLET = "\033[38;5;135m"  # 紫罗兰色
    GOLD = "\033[38;5;220m"  # 金色
    SILVER = "\033[38;5;240m"  # 银色

    # 背景色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # 亮色调背景色
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"

    # 创新背景色
    BG_ORANGE = "\033[48;5;208m"
    BG_PINK = "\033[48;5;219m"
    BG_PURPLE = "\033[48;5;129m"
    BG_TEAL = "\033[48;5;30m"

    # 样式
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKETHROUGH = "\033[9m"


class TerminalUtils:
    """终端交互工具类"""

    @staticmethod
    def colored(text, color=Color.RESET, style=None):
        """为文本添加颜色和样式"""
        # 现代 Windows 终端（如 Windows Terminal、PowerShell 7+）支持 ANSI 颜色
        # 不再需要为 Windows 系统禁用颜色
        color_code = color.value
        style_code = style.value if style else ""
        return f"{style_code}{color_code}{text}{Color.RESET.value}"

    @staticmethod
    def print_status(message, status="INFO"):
        """打印带状态的消息 - 创新配色"""
        status_colors = {
            "INFO": Color.BRIGHT_BLUE,  # 亮蓝色
            "SUCCESS": Color.BRIGHT_GREEN,  # 亮绿色
            "WARNING": Color.ORANGE,  # 橙色（创新）
            "ERROR": Color.BRIGHT_RED,  # 亮红色
            "DEBUG": Color.BRIGHT_MAGENTA,  # 亮紫色
            "CRITICAL": Color.PINK,  # 粉色（创新）
            "NOTICE": Color.BRIGHT_CYAN,  # 亮青色
            "VERBOSE": Color.SILVER,  # 银色（创新）
        }

        color = status_colors.get(status, Color.WHITE)
        timestamp = time.strftime("%H:%M:%S")
        # 使用创新的格式
        print(
            f"{TerminalUtils.colored('[', Color.GOLD)}"
            f"{TerminalUtils.colored(timestamp, Color.BRIGHT_WHITE)}"
            f"{TerminalUtils.colored(']', Color.GOLD)} "
            f"{TerminalUtils.colored(status, color, Color.BOLD)}"
            f"{TerminalUtils.colored(':', Color.GOLD)} {message}"
        )

    @staticmethod
    def progress_bar(current, total, prefix="", suffix="", length=50, fill="█", show_eta=True):
        """显示进度条 - 创新配色，支持预计剩余时间
        
        Args:
            current: 当前进度
            total: 总进度
            prefix: 前缀文本
            suffix: 后缀文本
            length: 进度条长度
            fill: 进度条填充字符
            show_eta: 是否显示预计剩余时间
        """
        percent = 100 * (current / float(total))
        filled_length = int(length * current // total)
        bar = fill * filled_length + "-" * (length - filled_length)

        if percent < 20:
            color = Color.BRIGHT_RED
        elif percent < 40:
            color = Color.ORANGE
        elif percent < 60:
            color = Color.BRIGHT_YELLOW
        elif percent < 80:
            color = Color.LIME
        else:
            color = Color.BRIGHT_GREEN

        eta_text = ""
        if show_eta and current > 0 and current < total:
            elapsed_time = time.time() - TerminalUtils._progress_start_time
            if hasattr(TerminalUtils, '_progress_start_time'):
                time_per_item = elapsed_time / current
                remaining_items = total - current
                eta_seconds = time_per_item * remaining_items
                
                if eta_seconds < 60:
                    eta_text = f" 预计剩余: {eta_seconds:.1f}秒"
                elif eta_seconds < 3600:
                    eta_text = f" 预计剩余: {eta_seconds/60:.1f}分钟"
                else:
                    eta_text = f" 预计剩余: {eta_seconds/3600:.1f}小时"

        sys.stdout.write(
            f"\r{TerminalUtils.colored(prefix, Color.BRIGHT_CYAN)} "
            f'{TerminalUtils.colored("[", Color.GOLD)}'
            f"{TerminalUtils.colored(bar, color, Color.BOLD)}"
            f'{TerminalUtils.colored("]", Color.GOLD)} '
            f'{TerminalUtils.colored(f"{percent:.1f}%", Color.BRIGHT_WHITE, Color.BOLD)} '
            f"{TerminalUtils.colored(suffix, Color.PURPLE)}{TerminalUtils.colored(eta_text, Color.SILVER)}"
        )
        sys.stdout.flush()

        if current == 0:
            TerminalUtils._progress_start_time = time.time()
        
        if current == total:
            if hasattr(TerminalUtils, '_progress_start_time'):
                total_time = time.time() - TerminalUtils._progress_start_time
                del TerminalUtils._progress_start_time
                print(f" {TerminalUtils.colored('[✓]', Color.BRIGHT_GREEN)} "
                      f"{TerminalUtils.colored(f'完成! 耗时: {total_time:.1f}秒', Color.BRIGHT_GREEN)}")

    @staticmethod
    def spinner(iterable, prefix="处理中", suffix=""):
        """带旋转动画的迭代器 - 创新配色"""
        # 创新的旋转字符
        spinner_chars = ["◐", "◓", "◑", "◒"]  # 圆形旋转
        # spinner_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']  # 进度条旋转
        total = len(iterable)

        for i, item in enumerate(iterable):
            spinner_char = spinner_chars[i % len(spinner_chars)]
            percent = 100 * (i / float(total))

            # 创新的旋转动画格式
            sys.stdout.write(
                f"\r{TerminalUtils.colored(prefix, Color.BRIGHT_CYAN)} "
                f"{TerminalUtils.colored(spinner_char, Color.ORANGE, Color.BOLD)} "
                f'{TerminalUtils.colored(f"{percent:.1f}%", Color.BRIGHT_WHITE, Color.BOLD)} '
                f"{TerminalUtils.colored(suffix, Color.PURPLE)}"
            )
            sys.stdout.flush()
            yield item

        # 完成时添加成功提示
        print(f" {TerminalUtils.colored('[✓]', Color.BRIGHT_GREEN)}")

    @staticmethod
    def clear_screen():
        """清屏"""
        import os

        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def pause(message="按 Enter 键继续..."):
        """暂停并等待用户输入"""
        input(message)

    @staticmethod
    def _calculate_column_widths(data: List[Dict], headers: List[str]) -> Dict[str, int]:
        """计算每列的最大宽度
        
        Args:
            data: 表格数据列表
            headers: 表头列表
            
        Returns:
            Dict[str, int]: 每列的最大宽度字典
        """
        column_widths = {}
        for header in headers:
            column_widths[header] = len(str(header))
            for row in data:
                cell_value = row.get(header, "")
                cell_width = len(str(cell_value))
                if cell_width > column_widths[header]:
                    column_widths[header] = cell_width
        return column_widths

    @staticmethod
    def _build_separator(column_widths: Dict[str, int], headers: List[str], 
                          left_char: str, mid_char: str, right_char: str) -> str:
        """构建表格分隔线
        
        Args:
            column_widths: 列宽度字典
            headers: 表头列表
            left_char: 左边字符
            mid_char: 中间字符
            right_char: 右边字符
            
        Returns:
            str: 分隔线字符串
        """
        horizontal_line = "─"
        separator = left_char
        for i, header in enumerate(headers):
            width = column_widths[header]
            separator += horizontal_line * (width + 2)
            if i < len(headers) - 1:
                separator += mid_char
            else:
                separator += right_char
        return separator

    @staticmethod
    def _format_cell(value: Any, width: int, align: str) -> str:
        """格式化单元格内容
        
        Args:
            value: 单元格值
            width: 列宽度
            align: 对齐方式
            
        Returns:
            str: 格式化后的字符串
        """
        value_str = str(value)
        cell_align = align
        if isinstance(value, (int, float)):
            cell_align = "right"
        
        if cell_align == "left":
            return value_str.ljust(width)
        elif cell_align == "right":
            return value_str.rjust(width)
        else:
            return value_str.center(width)

    @staticmethod
    def print_table(data: List[Dict], headers: List[str] = None, align: str = "left", 
                    title: str = None, alternate_rows: bool = True) -> None:
        """打印格式化表格 - 重构版本
        
        Args:
            data: 表格数据列表
            headers: 表头列表，默认使用数据的键
            align: 对齐方式，默认左对齐
            title: 表格标题
            alternate_rows: 是否交替行颜色
        """
        if not data:
            return

        if not headers:
            headers = list(data[0].keys())

        column_widths = TerminalUtils._calculate_column_widths(data, headers)

        top_separator = TerminalUtils._build_separator(column_widths, headers, "┌", "┬", "┐")
        header_separator = TerminalUtils._build_separator(column_widths, headers, "├", "┼", "┤")
        bottom_separator = TerminalUtils._build_separator(column_widths, headers, "└", "┴", "┘")

        total_width = sum(column_widths.values()) + len(headers) * 3 + 1

        if title:
            title_line = f"{title}"
            print(TerminalUtils.colored(title_line.center(total_width), Color.BRIGHT_CYAN, Color.BOLD))
            print(TerminalUtils.colored("─" * total_width, Color.BRIGHT_CYAN))

        print(TerminalUtils.colored(top_separator, Color.BRIGHT_CYAN))

        header_line = "│"
        for header in headers:
            width = column_widths[header]
            header_line += f" {TerminalUtils.colored(header.center(width), Color.BRIGHT_WHITE, Color.BOLD)} "
            header_line += "│"
        print(TerminalUtils.colored(header_line, Color.BRIGHT_CYAN))

        print(TerminalUtils.colored(header_separator, Color.BRIGHT_CYAN))

        for i, row in enumerate(data):
            row_line = "│"
            row_color = Color.WHITE if not alternate_rows or i % 2 == 0 else Color.SILVER
            for header in headers:
                width = column_widths[header]
                value = row.get(header, "")
                formatted_value = TerminalUtils._format_cell(value, width, align)
                row_line += f" {TerminalUtils.colored(formatted_value, row_color)} "
                row_line += "│"
            print(TerminalUtils.colored(row_line, Color.BRIGHT_CYAN))

        print(TerminalUtils.colored(bottom_separator, Color.BRIGHT_CYAN))
        
        if data:
            stats_line = f" 共 {len(data)} 行数据 "
            print(TerminalUtils.colored(stats_line.rjust(total_width), Color.SILVER))

    @staticmethod
    def print_step(step_number, total_steps, description):
        """打印步骤信息 - 创新配色"""
        # 创新的步骤格式
        print(
            f"\n{TerminalUtils.colored('┌', Color.GOLD)}"
            f"{TerminalUtils.colored('─' * 20, Color.BRIGHT_CYAN)}"
            f"{TerminalUtils.colored('┐', Color.GOLD)}"
        )
        print(
            f"{TerminalUtils.colored('│', Color.GOLD)} "
            f"{TerminalUtils.colored(f'Step {step_number}/{total_steps}', Color.BRIGHT_WHITE, Color.BOLD)} "
            f"{TerminalUtils.colored('│', Color.GOLD)}"
        )
        print(
            f"{TerminalUtils.colored('└', Color.GOLD)}"
            f"{TerminalUtils.colored('─' * 20, Color.BRIGHT_CYAN)}"
            f"{TerminalUtils.colored('┘', Color.GOLD)}"
        )
        print(
            f"{TerminalUtils.colored('  ▶', Color.ORANGE, Color.BOLD)} "
            f"{TerminalUtils.colored(description, Color.BRIGHT_WHITE)}"
        )

    @staticmethod
    def get_input(prompt, default=None, validator=None):
        """获取用户输入，支持默认值和验证器 - 创新配色"""
        while True:
            if default is not None:
                # 创新的输入提示格式
                prompt_text = (
                    f"{TerminalUtils.colored('▶', Color.ORANGE, Color.BOLD)} "
                    f"{TerminalUtils.colored(prompt, Color.BRIGHT_WHITE, Color.BOLD)} "
                    f"{TerminalUtils.colored('(', Color.SILVER)}default: {default}{TerminalUtils.colored(')', Color.SILVER)}: "
                )
                user_input = input(prompt_text)
                if not user_input:
                    return default
            else:
                # 创新的输入提示格式
                prompt_text = (
                    f"{TerminalUtils.colored('▶', Color.ORANGE, Color.BOLD)} "
                    f"{TerminalUtils.colored(prompt, Color.BRIGHT_WHITE, Color.BOLD)}: "
                )
                user_input = input(prompt_text)

            if validator is None:
                return user_input

            try:
                if validator(user_input):
                    return user_input
                else:
                    print(
                        f"  {TerminalUtils.colored('[✗]', Color.BRIGHT_RED)} "
                        f"{TerminalUtils.colored('输入无效，请重新输入！', Color.BRIGHT_RED)}"
                    )
            except Exception as e:
                print(
                    f"  {TerminalUtils.colored('[✗]', Color.BRIGHT_RED)} "
                    f"{TerminalUtils.colored(f'输入错误: {e}', Color.BRIGHT_RED)}"
                )

    @staticmethod
    def print_error(message, error_code=None, suggestion=None, severity="error"):
        """打印用户友好的错误提示
        
        Args:
            message: 错误描述信息
            error_code: 错误代码（可选）
            suggestion: 解决建议（可选）
            severity: 严重程度，可选值为 'error', 'warning', 'info'
        """
        severity_colors = {
            "error": Color.BRIGHT_RED,
            "warning": Color.ORANGE,
            "info": Color.BRIGHT_BLUE
        }
        
        severity_symbols = {
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ"
        }
        
        color = severity_colors.get(severity, Color.BRIGHT_RED)
        symbol = severity_symbols.get(severity, "✗")
        
        print(f"\n{TerminalUtils.colored('┌' + '─' * 50, color)}")
        print(f"{TerminalUtils.colored('│', color)} {TerminalUtils.colored(f'{symbol} {message}', color, Color.BOLD)}")
        
        if error_code:
            print(f"{TerminalUtils.colored('│', color)} {TerminalUtils.colored(f'错误代码: {error_code}', Color.SILVER)}")
        
        if suggestion:
            print(f"{TerminalUtils.colored('│', color)} {TerminalUtils.colored('💡 建议: ' + suggestion, Color.BRIGHT_YELLOW)}")
        
        print(f"{TerminalUtils.colored('└' + '─' * 50, color)}\n")

    @staticmethod
    def print_success(message):
        """打印成功消息"""
        print(f"\n{TerminalUtils.colored('✓', Color.BRIGHT_GREEN, Color.BOLD)} "
              f"{TerminalUtils.colored(message, Color.BRIGHT_GREEN)}\n")

    @staticmethod
    def print_warning(message, suggestion=None):
        """打印警告消息"""
        print(f"\n{TerminalUtils.colored('⚠', Color.ORANGE, Color.BOLD)} "
              f"{TerminalUtils.colored(message, Color.ORANGE)}")
        if suggestion:
            print(f"  {TerminalUtils.colored('💡 建议: ' + suggestion, Color.BRIGHT_YELLOW)}\n")

    @staticmethod
    def print_info(message):
        """打印信息消息"""
        print(f"\n{TerminalUtils.colored('ℹ', Color.BRIGHT_BLUE, Color.BOLD)} "
              f"{TerminalUtils.colored(message, Color.BRIGHT_BLUE)}\n")

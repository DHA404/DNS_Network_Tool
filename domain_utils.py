#!/usr/bin/env python3
# 域名处理工具模块

import re
import os
from terminal_utils import TerminalUtils, Color


class DomainValidator:
    """域名验证类"""

    # 域名正则表达式（符合 RFC 1035 规范）
    DOMAIN_PATTERN = re.compile(r"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")

    # 常见顶级域名列表
    COMMON_TLDS = [
        "com",
        "org",
        "net",
        "edu",
        "gov",
        "mil",
        "int",
        "info",
        "biz",
        "name",
        "pro",
        "aero",
        "coop",
        "museum",
        "asia",
        "cat",
        "jobs",
        "mobi",
        "tel",
        "travel",
        "xxx",
        "ac",
        "ad",
        "ae",
        "af",
        "ag",
        "ai",
        "al",
        "am",
        "an",
        "ao",
        "aq",
        "ar",
        "as",
        "at",
        "au",
        "aw",
        "ax",
        "az",
        "ba",
        "bb",
        "bd",
        "be",
        "bf",
        "bg",
        "bh",
        "bi",
        "bj",
        "bm",
        "bn",
        "bo",
        "br",
        "bs",
        "bt",
        "bv",
        "bw",
        "by",
        "bz",
        "ca",
        "cc",
        "cd",
        "cf",
        "cg",
        "ch",
        "ci",
        "ck",
        "cl",
        "cm",
        "cn",
        "co",
        "cr",
        "cu",
        "cv",
        "cx",
        "cy",
        "cz",
        "de",
        "dj",
        "dk",
        "dm",
        "do",
        "dz",
        "ec",
        "ee",
        "eg",
        "eh",
        "er",
        "es",
        "et",
        "eu",
        "fi",
        "fj",
        "fk",
        "fm",
        "fo",
        "fr",
        "ga",
        "gb",
        "gd",
        "ge",
        "gf",
        "gg",
        "gh",
        "gi",
        "gl",
        "gm",
        "gn",
        "gp",
        "gq",
        "gr",
        "gs",
        "gt",
        "gu",
        "gw",
        "gy",
        "hk",
        "hm",
        "hn",
        "hr",
        "ht",
        "hu",
        "id",
        "ie",
        "il",
        "im",
        "in",
        "io",
        "iq",
        "ir",
        "is",
        "it",
        "je",
        "jm",
        "jo",
        "jp",
        "ke",
        "kg",
        "kh",
        "ki",
        "km",
        "kn",
        "kp",
        "kr",
        "kw",
        "ky",
        "kz",
        "la",
        "lb",
        "lc",
        "li",
        "lk",
        "lr",
        "ls",
        "lt",
        "lu",
        "lv",
        "ly",
        "ma",
        "mc",
        "md",
        "me",
        "mg",
        "mh",
        "mk",
        "ml",
        "mm",
        "mn",
        "mo",
        "mp",
        "mq",
        "mr",
        "ms",
        "mt",
        "mu",
        "mv",
        "mw",
        "mx",
        "my",
        "mz",
        "na",
        "nc",
        "ne",
        "nf",
        "ng",
        "ni",
        "nl",
        "no",
        "np",
        "nr",
        "nu",
        "nz",
        "om",
        "pa",
        "pe",
        "pf",
        "pg",
        "ph",
        "pk",
        "pl",
        "pm",
        "pn",
        "pr",
        "ps",
        "pt",
        "pw",
        "py",
        "qa",
        "re",
        "ro",
        "rs",
        "ru",
        "rw",
        "sa",
        "sb",
        "sc",
        "sd",
        "se",
        "sg",
        "sh",
        "si",
        "sj",
        "sk",
        "sl",
        "sm",
        "sn",
        "so",
        "sr",
        "st",
        "su",
        "sv",
        "sy",
        "sz",
        "tc",
        "td",
        "tf",
        "tg",
        "th",
        "tj",
        "tk",
        "tl",
        "tm",
        "tn",
        "to",
        "tp",
        "tr",
        "tt",
        "tv",
        "tw",
        "tz",
        "ua",
        "ug",
        "uk",
        "us",
        "uy",
        "uz",
        "va",
        "vc",
        "ve",
        "vg",
        "vi",
        "vn",
        "vu",
        "wf",
        "ws",
        "ye",
        "yt",
        "za",
        "zm",
        "zw",
    ]

    @staticmethod
    def is_valid_domain(domain):
        """验证域名格式是否有效"""
        if not domain:
            return False, "域名不能为空"

        # 检查长度
        if len(domain) > 253:
            return False, "域名长度不能超过253个字符"

        # 检查正则表达式
        if not DomainValidator.DOMAIN_PATTERN.match(domain):
            return False, "域名格式不符合规范"

        # 检查每个标签长度
        labels = domain.split(".")
        for label in labels:
            if len(label) > 63:
                return False, f"域名标签 '{label}' 长度不能超过63个字符"
        
        # 检查顶级域名（允许所有有效的 TLD，只显示警告）
        tld = labels[-1].lower()
        if tld not in DomainValidator.COMMON_TLDS:
            return True, "域名格式有效（警告：非常见顶级域名）"
        
        return True, "域名格式有效"

    @staticmethod
    def normalize_domain(domain):
        """标准化域名（转换为小写，去除首尾空格）"""
        return domain.strip().lower()

    @staticmethod
    def suggest_fix(domain):
        """提供域名修正建议"""
        suggestions = []

        # 检查是否缺少顶级域名
        if "." not in domain:
            suggestions.append(f"可能缺少顶级域名，例如: {domain}.com")

        # 检查是否有多余的空格
        if " " in domain:
            suggestions.append(f"域名中不应包含空格，建议: {domain.replace(' ', '')}")

        # 检查是否有特殊字符
        if re.search(r"[^a-zA-Z0-9.-]", domain):
            clean_domain = re.sub(r"[^a-zA-Z0-9.-]", "", domain)
            suggestions.append(f"域名中包含特殊字符，建议: {clean_domain}")

        return suggestions


class DomainInputHandler:
    """域名输入处理类"""

    @staticmethod
    def get_single_domain():
        """获取单个域名输入"""
        while True:
            domain = input("请输入域名: ")
            normalized_domain = DomainValidator.normalize_domain(domain)

            if not normalized_domain:
                print(TerminalUtils.colored("域名不能为空，请重新输入！", Color.RED))
                continue

            is_valid, message = DomainValidator.is_valid_domain(normalized_domain)
            if is_valid:
                TerminalUtils.print_status(f"域名 '{normalized_domain}' 格式验证通过", "SUCCESS")
                return normalized_domain
            else:
                print(TerminalUtils.colored(f"域名验证失败: {message}", Color.RED))
                suggestions = DomainValidator.suggest_fix(normalized_domain)
                if suggestions:
                    print(TerminalUtils.colored("建议修正:", Color.YELLOW))
                    for suggestion in suggestions:
                        print(f"  - {suggestion}")

    @staticmethod
    def get_batch_domains_from_file(file_path):
        """从文件中获取批量域名，自动去除重复项"""
        domains = set()
        invalid_domains = []
        warning_domains = []

        try:
            if not os.path.exists(file_path):
                print(TerminalUtils.colored(f"文件 '{file_path}' 不存在！", Color.RED))
                return [], [], []

            if not file_path.endswith(".txt"):
                print(TerminalUtils.colored("仅支持 .txt 格式文件！", Color.RED))
                return [], [], []

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            total_lines = len(lines)
            print(f"共读取 {total_lines} 行数据")

            for i, line in enumerate(lines, 1):
                domain = DomainValidator.normalize_domain(line)
                if not domain:
                    continue

                is_valid, message = DomainValidator.is_valid_domain(domain)
                if is_valid:
                    domains.add(domain)
                    if "警告" in message:
                        warning_domains.append((i, domain, message))
                else:
                    invalid_domains.append((i, domain, message))

            return list(domains), invalid_domains, warning_domains

        except Exception as e:
            print(TerminalUtils.colored(f"读取文件时出错: {str(e)}", Color.RED))
            return [], [], []

    @staticmethod
    def get_batch_domains_from_input():
        """从输入中获取批量域名，支持逗号分隔和空行分隔，自动去除重复项"""
        print("请输入域名，支持用逗号（,）、中文逗号（，）分隔或每行一个域名，输入完成后按Enter键两次:")
        domains = set()
        invalid_domains = []
        warning_domains = []

        input_lines = []
        while True:
            line = input()
            if not line:
                break
            input_lines.append(line)

        line_number = 1
        import re

        for line in input_lines:
            domain_list = re.split(r"[,，]+", line)

            for domain_str in domain_list:
                domain = DomainValidator.normalize_domain(domain_str)
                if not domain:
                    continue

                is_valid, message = DomainValidator.is_valid_domain(domain)
                if is_valid:
                    domains.add(domain)
                    if "警告" in message:
                        warning_domains.append((line_number, domain, message))
                else:
                    invalid_domains.append((line_number, domain, message))

            line_number += 1

        return list(domains), invalid_domains, warning_domains

    @staticmethod
    def display_validation_results(domains, invalid_domains, warning_domains=None):
        """显示域名验证结果"""
        if warning_domains is None:
            warning_domains = []
        
        print(TerminalUtils.colored("\n=== 域名验证结果 ===", Color.CYAN, Color.BOLD))

        total_valid = len(domains) + len(warning_domains)
        
        if total_valid > 0:
            print(TerminalUtils.colored(f"✓ 有效域名: {total_valid} 个（包含 {len(warning_domains)} 个非常见TLD域名）", Color.GREEN))
            all_valid_domains = domains + [d[1] for d in warning_domains]
            for domain in all_valid_domains:
                print(f"  - {domain}")
        else:
            print(TerminalUtils.colored("未发现有效域名", Color.YELLOW))

        if invalid_domains:
            print(TerminalUtils.colored(f"\n✗ 无效域名: {len(invalid_domains)} 个", Color.RED))
            for line_num, domain, error in invalid_domains:
                print(f"  - 行 {line_num}: {domain} (错误: {error})")

        return total_valid > 0

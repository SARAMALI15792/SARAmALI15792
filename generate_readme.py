import os, subprocess, sys

# URLs for dynamic badges (same as used in the README)
BADGE_URLS = {
    "profile_stats": "https://github-readme-stats.vercel.app/api?username=SARAMALI15792&theme=tokyonight&hide_border=true&include_all_commits=true&count_private=true&show_icons=true",
    "streak": "https://nirzak-streak-stats.vercel.app/?user=SARAMALI15792&theme=tokyonight&hide_border=true",
    "top_langs": "https://github-readme-stats.vercel.app/api/top-langs/?username=SARAMALI15792&theme=tokyonight&hide_border=true&include_all_commits=true&count_private=true&layout=compact",
    "contrib_snake": "https://profile-readme-generator.com/assets/snake.svg",
    "quote": "https://quotes-github-readme.vercel.app/api?type=horizontal&theme=tokyonight",
    # Typing animation – kept static as before
    "typing": "https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&size=24&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&width=600&lines=I+write+specs+first%2C+then+let+AI+ship+the+code.;Building+AI+agents+that+actually+work.;SDD-RI+%7C+Claude+Code+%7C+MCP+Servers;5+years+of+code.+Infinite+curiosity.",
}

def generate_section(header: str, content: str) -> str:
    return f"## {header}\n\n{content}\n"

def main():
    # Build the README content step by step – matching the current layout but using the same URLs.
    parts = []

    # Hero header (new SVG)
    parts.append("<div align=\"center\"><img src=\"./profile-header.svg\" alt=\"Saram Ali — Agentic AI Engineer\" width=\"100%\"/></div>\n\n---\n")

    # Typing animation
    parts.append(f"![Typing SVG]({BADGE_URLS['typing']})\n\n---\n")

    # Intro
    parts.append("## 🧠 Who Am I?\n\nHey — I'm **Saram Ali** from Rawalpindi, Pakistan 🇵🇰\n\nI've been writing code for **5 years**, focusing on building AI agents that are reliable, testable, and ship to production.\n\n---\n")

    # Featured Projects (static list, kept as‑is for now)
    parts.append("## 🚀 Featured Projects\n\n<!-- Add your projects here -->\n---\n")

    # Tech Stack (static badges)
    parts.append("## 💻 Tech Stack\n\n<!-- Keep existing badge shields -->\n---\n")

    # Stats (dynamic images)
    stats_section = f"<div align=\"center\">\n![Profile Stats]({BADGE_URLS['profile_stats']})\n![Streak]({BADGE_URLS['streak']})\n![Top Languages]({BADGE_URLS['top_langs']})\n</div>\n"
    parts.append(stats_section)

    # Contribution snake and quote
    parts.append(f"![Contribution Snake]({BADGE_URLS['contrib_snake']})\n\n![]({BADGE_URLS['quote']})\n")

    # Contact
    parts.append("## 📬 Connect\n\n[LinkedIn](https://linkedin.com/in/saramali) | [GitHub](https://github.com/SARAMALI15792)\n")

    readme_content = "\n".join(parts)

    # Write to README.md in the repo root
    readme_path = os.path.join(os.getcwd(), "SARAmALI15792", "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Generated README at {readme_path}")

if __name__ == "__main__":
    main()

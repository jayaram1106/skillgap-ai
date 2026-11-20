"""
SkillGap AI - Curated Technical Skill Dictionary.

Provides normalized canonical names, categories, aliases, and robust regular
expression patterns to accurately detect skills in resumes and job descriptions
without false positives or substring collisions.
"""

from typing import Dict, List, TypedDict, Pattern
import re


class SkillDefinition(TypedDict):
    canonical: str
    category: str
    aliases: List[str]
    pattern: Pattern


# ---------------------------------------------------------------------------
# Curated Skill Definitions
# ---------------------------------------------------------------------------
# Categories:
#   1. Programming Languages
#   2. Frontend Development
#   3. Backend Development & APIs
#   4. Databases & Storage
#   5. Cloud, DevOps & Infrastructure
#   6. Tools & Practices
#   7. Core Computer Science
# ---------------------------------------------------------------------------

SKILL_DEFINITIONS: List[SkillDefinition] = [
    # -----------------------------------------------------------------------
    # 1. Programming Languages
    # -----------------------------------------------------------------------
    {
        "canonical": "Python",
        "category": "Programming Languages",
        "aliases": ["Python", "Python3", "Python 3"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])python(?:3)?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "JavaScript",
        "category": "Programming Languages",
        "aliases": ["JavaScript", "JS", "ECMAScript", "ES6"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:javascript|js|ecmascript|es6|es20\d\d)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "TypeScript",
        "category": "Programming Languages",
        "aliases": ["TypeScript", "TS"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:typescript|ts)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Java",
        "category": "Programming Languages",
        "aliases": ["Java", "Core Java", "Java 8", "Java 11", "Java 17", "Java 21"],
        # Negative lookahead prevents matching JavaScript
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])java(?![a-zA-Z0-9_])(?!\s*script)",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "C++",
        "category": "Programming Languages",
        "aliases": ["C++", "Cpp", "C Plus Plus"],
        # Characters like + are not word boundaries, so custom lookarounds are used
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:c\+\+|cpp|c\s+plus\s+plus)(?![a-zA-Z0-9_+])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "C#",
        "category": "Programming Languages",
        "aliases": ["C#", "CSharp", "C-Sharp"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:c#|csharp|c-sharp|c\s+sharp)(?![a-zA-Z0-9_#])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "C",
        "category": "Programming Languages",
        "aliases": ["C Language", "C Programming", "ANSI C"],
        # Precise matching for single-letter language C to prevent false positives
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:c\s+programming|c\s+language|ansi\s+c)(?![a-zA-Z0-9_])|"
            r"(?<![a-zA-Z0-9_])C(?![a-zA-Z0-9_])(?=\s*[/,]\s*(?:C\+\+|C#|Java|Python|Assembly))"
        ),
    },
    {
        "canonical": "Go",
        "category": "Programming Languages",
        "aliases": ["Go", "Golang", "Go Language"],
        # Avoid matching common English verb 'go'
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:[Gg]olang|[Gg]o\s+(?:programming|language|backend|developer|code))(?![a-zA-Z0-9_])|"
            r"(?<![a-zA-Z0-9_])Go(?![a-zA-Z0-9_])(?=[\s,;/]+(?:Python|Java|Rust|C\+\+|Docker|Kubernetes|Backend|PostgreSQL|AWS|SQL))"
        ),
    },
    {
        "canonical": "Rust",
        "category": "Programming Languages",
        "aliases": ["Rust", "Rustlang"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:rust|rustlang)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Ruby",
        "category": "Programming Languages",
        "aliases": ["Ruby"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])ruby(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "PHP",
        "category": "Programming Languages",
        "aliases": ["PHP", "PHP7", "PHP8"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])php(?:7|8)?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Swift",
        "category": "Programming Languages",
        "aliases": ["Swift", "SwiftUI"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:swift|swiftui)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Kotlin",
        "category": "Programming Languages",
        "aliases": ["Kotlin"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])kotlin(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Scala",
        "category": "Programming Languages",
        "aliases": ["Scala"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])scala(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "R",
        "category": "Programming Languages",
        "aliases": ["R Language", "R Programming", "RStudio"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:r\s+programming|r\s+language|rstudio)(?![a-zA-Z0-9_])|"
            r"(?<![a-zA-Z0-9_])R(?![a-zA-Z0-9_])(?=\s*[/,]\s*(?:Python|SQL|Julia|SAS|MATLAB))"
        ),
    },
    {
        "canonical": "Dart",
        "category": "Programming Languages",
        "aliases": ["Dart"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])dart(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "SQL",
        "category": "Programming Languages",
        "aliases": ["SQL", "Structured Query Language"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:sql|structured\s+query\s+language)(?![a-zA-Z0-9_])(?!\s*server)",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Shell Scripting",
        "category": "Programming Languages",
        "aliases": ["Bash", "Shell", "Shell Scripting", "Zsh"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:bash|shell\s+script(?:ing)?|zsh)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },

    # -----------------------------------------------------------------------
    # 2. Frontend Development
    # -----------------------------------------------------------------------
    {
        "canonical": "React",
        "category": "Frontend",
        "aliases": ["React", "React.js", "ReactJS"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:react|react\.?js|reactjs)(?![a-zA-Z0-9_])(?!\s*native)",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Next.js",
        "category": "Frontend",
        "aliases": ["Next.js", "NextJS", "Next js"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:next\.?js|nextjs)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Angular",
        "category": "Frontend",
        "aliases": ["Angular", "AngularJS", "Angular 2+"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:angular|angularjs)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Vue.js",
        "category": "Frontend",
        "aliases": ["Vue", "Vue.js", "VueJS", "Vue 3"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:vue|vue\.?js|vuejs)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Nuxt.js",
        "category": "Frontend",
        "aliases": ["Nuxt", "Nuxt.js", "NuxtJS"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:nuxt|nuxt\.?js|nuxtjs)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Svelte",
        "category": "Frontend",
        "aliases": ["Svelte", "SvelteKit"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:svelte|sveltekit)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "HTML",
        "category": "Frontend",
        "aliases": ["HTML", "HTML5"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])html5?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "CSS",
        "category": "Frontend",
        "aliases": ["CSS", "CSS3"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])css3?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Tailwind CSS",
        "category": "Frontend",
        "aliases": ["Tailwind", "TailwindCSS", "Tailwind CSS"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:tailwind|tailwindcss|tailwind\s+css)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Bootstrap",
        "category": "Frontend",
        "aliases": ["Bootstrap", "Bootstrap 5"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])bootstrap(?:5)?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Redux",
        "category": "Frontend",
        "aliases": ["Redux", "Redux Toolkit", "RTK"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:redux(?:\s+toolkit)?|rtk)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Sass",
        "category": "Frontend",
        "aliases": ["Sass", "SCSS"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:sass|scss)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "jQuery",
        "category": "Frontend",
        "aliases": ["jQuery"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])jquery(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Webpack",
        "category": "Frontend",
        "aliases": ["Webpack"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])webpack(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Vite",
        "category": "Frontend",
        "aliases": ["Vite"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])vite(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },

    # -----------------------------------------------------------------------
    # 3. Backend Development & APIs
    # -----------------------------------------------------------------------
    {
        "canonical": "FastAPI",
        "category": "Backend",
        "aliases": ["FastAPI", "Fast API"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:fastapi|fast\s+api)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Django",
        "category": "Backend",
        "aliases": ["Django", "Django REST Framework", "DRF"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:django(?:\s+rest\s+framework)?|drf)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Flask",
        "category": "Backend",
        "aliases": ["Flask"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])flask(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Node.js",
        "category": "Backend",
        "aliases": ["Node.js", "NodeJS", "Node js"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:node\.?js|nodejs)(?![a-zA-Z0-9_])|"
            r"(?<![a-zA-Z0-9_])node(?![a-zA-Z0-9_])(?=\s*(?:js|backend|runtime|server|express))",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Express.js",
        "category": "Backend",
        "aliases": ["Express.js", "ExpressJS", "Express Framework"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:express\.?js|expressjs)(?![a-zA-Z0-9_])|"
            r"(?<![a-zA-Z0-9_])express(?![a-zA-Z0-9_])(?=\s*(?:framework|server|backend|middleware))",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Spring Boot",
        "category": "Backend",
        "aliases": ["Spring Boot", "SpringBoot", "Spring Framework"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:spring\s+boot|springboot|spring\s+framework)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "ASP.NET Core",
        "category": "Backend",
        "aliases": ["ASP.NET", "ASP.NET Core", ".NET Core"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:asp\.net(?:\s+core)?|\.net(?:\s+core)?)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Ruby on Rails",
        "category": "Backend",
        "aliases": ["Ruby on Rails", "Rails"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:ruby\s+on\s+rails|rails)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "NestJS",
        "category": "Backend",
        "aliases": ["NestJS", "Nest.js"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:nest\.?js|nestjs)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Laravel",
        "category": "Backend",
        "aliases": ["Laravel"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])laravel(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "REST APIs",
        "category": "Backend",
        "aliases": ["REST", "RESTful", "REST API", "REST APIs", "RESTful APIs"],
        # Prevents matching 'the rest of the team' while matching 'REST APIs' or uppercase 'REST'
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:rest(?:ful)?\s*(?:apis?|web\s*services?|services?|architecture|endpoints?)|restful)(?![a-zA-Z0-9_])|"
            r"(?<![a-zA-Z0-9_])REST(?![a-zA-Z0-9_])(?!\s+(?:of\b|assured\b|in\s+peace\b))"
        ),
    },
    {
        "canonical": "GraphQL",
        "category": "Backend",
        "aliases": ["GraphQL"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])graphql(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "gRPC",
        "category": "Backend",
        "aliases": ["gRPC"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])grpc(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Microservices",
        "category": "Backend",
        "aliases": ["Microservices", "Microservice Architecture"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])micro[- ]?services?(?:\s+architecture)?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Celery",
        "category": "Backend",
        "aliases": ["Celery"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])celery(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "WebSockets",
        "category": "Backend",
        "aliases": ["WebSocket", "WebSockets"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])websockets?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },

    # -----------------------------------------------------------------------
    # 4. Databases & Storage
    # -----------------------------------------------------------------------
    {
        "canonical": "PostgreSQL",
        "category": "Databases",
        "aliases": ["PostgreSQL", "Postgres", "Postgres DB", "PSQL"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:postgresql|postgres|postgres\s*db|psql)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "MySQL",
        "category": "Databases",
        "aliases": ["MySQL"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])mysql(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "SQLite",
        "category": "Databases",
        "aliases": ["SQLite", "SQLite3"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])sqlite(?:3)?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "MongoDB",
        "category": "Databases",
        "aliases": ["MongoDB", "Mongo", "MongoDB Atlas"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:mongodb|mongo(?:\s+db)?)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Redis",
        "category": "Databases",
        "aliases": ["Redis"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])redis(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Elasticsearch",
        "category": "Databases",
        "aliases": ["Elasticsearch", "Elastic Search"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:elasticsearch|elastic\s+search)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Cassandra",
        "category": "Databases",
        "aliases": ["Cassandra", "Apache Cassandra"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:apache\s+)?cassandra(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "DynamoDB",
        "category": "Databases",
        "aliases": ["DynamoDB", "Amazon DynamoDB"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:amazon\s+)?dynamodb(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Oracle Database",
        "category": "Databases",
        "aliases": ["Oracle DB", "Oracle Database"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])oracle\s+(?:db|database|rdbms)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Microsoft SQL Server",
        "category": "Databases",
        "aliases": ["SQL Server", "MSSQL", "MS SQL Server", "Microsoft SQL Server"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:microsoft\s+sql\s+server|sql\s+server|mssql|ms\s*sql)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Firebase",
        "category": "Databases",
        "aliases": ["Firebase", "Firestore"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:firebase|firestore)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Supabase",
        "category": "Databases",
        "aliases": ["Supabase"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])supabase(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "MariaDB",
        "category": "Databases",
        "aliases": ["MariaDB"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])mariadb(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Neo4j",
        "category": "Databases",
        "aliases": ["Neo4j"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])neo4j(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },

    # -----------------------------------------------------------------------
    # 5. Cloud, DevOps & Infrastructure
    # -----------------------------------------------------------------------
    {
        "canonical": "AWS",
        "category": "Cloud & DevOps",
        "aliases": ["AWS", "Amazon Web Services", "Amazon AWS"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:aws|amazon\s+web\s+services?|aws\s+lambda|amazon\s+ec2|amazon\s+s3)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Google Cloud",
        "category": "Cloud & DevOps",
        "aliases": ["Google Cloud", "Google Cloud Platform", "GCP"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:google\s+cloud(?:\s+platform)?|gcp)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Azure",
        "category": "Cloud & DevOps",
        "aliases": ["Azure", "Microsoft Azure"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:azure|microsoft\s+azure)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Docker",
        "category": "Cloud & DevOps",
        "aliases": ["Docker", "Dockerfile", "Docker Compose"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:docker|dockerfile|docker\s*compose|docker-compose)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Kubernetes",
        "category": "Cloud & DevOps",
        "aliases": ["Kubernetes", "K8s"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:kubernetes|k8s)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Terraform",
        "category": "Cloud & DevOps",
        "aliases": ["Terraform"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])terraform(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Ansible",
        "category": "Cloud & DevOps",
        "aliases": ["Ansible"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])ansible(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "CI/CD",
        "category": "Cloud & DevOps",
        "aliases": ["CI/CD", "CI CD", "Continuous Integration", "Continuous Deployment"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:ci\s*/\s*cd|ci-cd|continuous\s+integration(?:\s*(?:and|/|&)\s*(?:continuous\s*)?deployment)?)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "GitHub Actions",
        "category": "Cloud & DevOps",
        "aliases": ["GitHub Actions"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])github\s+actions(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Jenkins",
        "category": "Cloud & DevOps",
        "aliases": ["Jenkins"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])jenkins(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Linux",
        "category": "Cloud & DevOps",
        "aliases": ["Linux", "Ubuntu", "Debian", "CentOS", "RedHat"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:linux|ubuntu|debian|centos|redhat|rhel)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Nginx",
        "category": "Cloud & DevOps",
        "aliases": ["Nginx"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])nginx(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Prometheus",
        "category": "Cloud & DevOps",
        "aliases": ["Prometheus"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])prometheus(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Grafana",
        "category": "Cloud & DevOps",
        "aliases": ["Grafana"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])grafana(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Helm",
        "category": "Cloud & DevOps",
        "aliases": ["Helm"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])helm(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },

    # -----------------------------------------------------------------------
    # 6. Tools & Practices
    # -----------------------------------------------------------------------
    {
        "canonical": "Git",
        "category": "Tools & Practices",
        "aliases": ["Git"],
        # Prevents matching 'GitHub', 'GitLab', 'GitBucket' as bare Git
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])git(?![a-zA-Z0-9_])(?!\s*(?:hub|lab|bucket))",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "GitHub",
        "category": "Tools & Practices",
        "aliases": ["GitHub"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])github(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "GitLab",
        "category": "Tools & Practices",
        "aliases": ["GitLab"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])gitlab(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Bitbucket",
        "category": "Tools & Practices",
        "aliases": ["Bitbucket"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])bitbucket(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Jira",
        "category": "Tools & Practices",
        "aliases": ["Jira"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])jira(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Agile",
        "category": "Tools & Practices",
        "aliases": ["Agile", "Agile Methodology"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])agile(?:\s+methodolog(?:y|ies))?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Scrum",
        "category": "Tools & Practices",
        "aliases": ["Scrum"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])scrum(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Postman",
        "category": "Tools & Practices",
        "aliases": ["Postman"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])postman(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Unit Testing",
        "category": "Tools & Practices",
        "aliases": ["Unit Testing", "Unit Tests", "TDD"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:unit\s+test(?:ing|s)?|tdd|test\s+driven\s+development)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Pytest",
        "category": "Tools & Practices",
        "aliases": ["Pytest"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])pytest(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Jest",
        "category": "Tools & Practices",
        "aliases": ["Jest"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])jest(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },

    # -----------------------------------------------------------------------
    # 7. Core Computer Science Skills
    # -----------------------------------------------------------------------
    {
        "canonical": "Data Structures",
        "category": "Core Computer Science",
        "aliases": ["Data Structures"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])data\s+structures?(?![a-zA-Z0-9_])(?!\s*(?:and|&)\s*algorithms?)",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Algorithms",
        "category": "Core Computer Science",
        "aliases": ["Algorithms"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])algorithms?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Data Structures & Algorithms",
        "category": "Core Computer Science",
        "aliases": ["Data Structures and Algorithms", "DSA"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:data\s+structures?\s+(?:and|&)\s+algorithms?|dsa)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Object-Oriented Programming (OOP)",
        "category": "Core Computer Science",
        "aliases": ["OOP", "Object-Oriented Programming", "Object Oriented Programming"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:object[- ]oriented\s+programming|oop)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "System Design",
        "category": "Core Computer Science",
        "aliases": ["System Design", "Distributed Systems Design"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:system\s+design|distributed\s+systems?\s+design|high-level\s+design|low-level\s+design)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Design Patterns",
        "category": "Core Computer Science",
        "aliases": ["Design Patterns"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])design\s+patterns?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Database Design",
        "category": "Core Computer Science",
        "aliases": ["Database Design", "Schema Design"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:database\s+design|schema\s+design|relational\s+modeling)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Concurrency",
        "category": "Core Computer Science",
        "aliases": ["Concurrency", "Multithreading", "Asyncio"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:concurrency|multithreading|multi-threading|asynchronous\s+programming|asyncio)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Computer Networks",
        "category": "Core Computer Science",
        "aliases": ["Computer Networks", "TCP/IP"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])(?:computer\s+networks?|tcp\s*/\s*ip|network\s+protocols?)(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
    {
        "canonical": "Operating Systems",
        "category": "Core Computer Science",
        "aliases": ["Operating Systems"],
        "pattern": re.compile(
            r"(?<![a-zA-Z0-9_])operating\s+systems?(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        ),
    },
]


def get_skill_definitions() -> List[SkillDefinition]:
    """Return the list of all curated skill definitions."""
    return SKILL_DEFINITIONS


def get_categories() -> List[str]:
    """Return unique categories in curated dictionary."""
    seen = set()
    categories = []
    for s in SKILL_DEFINITIONS:
        cat = s["category"]
        if cat not in seen:
            seen.add(cat)
            categories.append(cat)
    return categories

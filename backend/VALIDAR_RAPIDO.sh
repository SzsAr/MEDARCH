#!/bin/bash

# Script de validación rápida - CRUD Usuarios MEDARCH
# Uso: bash VALIDAR_RAPIDO.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║ VALIDACIÓN RÁPIDA - CRUD USUARIOS MEDARCH                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador
ERRORS=0
SUCCESS=0

# PASO 1: Verificar Python
echo -e "${YELLOW}1. Verificando Python...${NC}"
python --version 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Python OK${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ Python no encontrado${NC}"
    ((ERRORS++))
fi
echo ""

# PASO 2: Verificar sintaxis
echo -e "${YELLOW}2. Verificando sintaxis de archivos...${NC}"
python -m py_compile app/api/routes/users.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ users.py OK${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ users.py tiene errores${NC}"
    python -m py_compile app/api/routes/users.py
    ((ERRORS++))
fi

python -m py_compile app/services/user_service.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ user_service.py OK${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ user_service.py tiene errores${NC}"
    python -m py_compile app/services/user_service.py
    ((ERRORS++))
fi
echo ""

# PASO 3: Verificar imports
echo -e "${YELLOW}3. Verificando imports...${NC}"
python -c "from app.api.routes.users import router" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ users.py importa OK${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ Error importando users.py${NC}"
    python -c "from app.api.routes.users import router"
    ((ERRORS++))
fi

python -c "from app.services.user_service import create_user" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ user_service.py importa OK${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ Error importando user_service.py${NC}"
    python -c "from app.services.user_service import create_user"
    ((ERRORS++))
fi
echo ""

# PASO 4: Verificar dependencias
echo -e "${YELLOW}4. Verificando dependencias...${NC}"
python -c "import fastapi" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ FastAPI instalado${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ FastAPI no instalado${NC}"
    ((ERRORS++))
fi

python -c "import pydantic" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Pydantic instalado${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ Pydantic no instalado${NC}"
    ((ERRORS++))
fi

python -c "import psycopg2" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ psycopg2 instalado${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}   ✗ psycopg2 no instalado${NC}"
    ((ERRORS++))
fi
echo ""

# RESUMEN
echo "╔════════════════════════════════════════════════════════════════╗"
echo -e "║ RESULTADO: ${GREEN}✓ $SUCCESS${NC}${YELLOW} OK ${NC}/ ${RED}✗ $ERRORS${NC}${YELLOW} Errores${NC}                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ VALIDACIÓN EXITOSA${NC}"
    echo ""
    echo "Próximo paso: Ejecutar servidor"
    echo "$ python main.py"
    echo "O"
    echo "$ uvicorn app.main:app --reload"
    exit 0
else
    echo ""
    echo -e "${RED}✗ VALIDACIÓN FALLIDA${NC}"
    echo ""
    echo "Ver documentación:"
    echo "- RESUMEN_DIAGNOSTICO.txt"
    echo "- ERRORES_DIAGNOSTICO.md"
    echo "- DIAGNOSTICO_CONSOLA.md"
    exit 1
fi

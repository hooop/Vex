#include <iostream>
#include <fstream>
#include <string>
#include <unistd.h>
#include <iterator>

// Codes ANSI pour les couleurs
/* #define RESET   "\033[0m"
#define BOLD    "\033[1m"
#define RED     "\033[38;5;205m"
#define GREEN   "\033[38;5;158m"
#define YELLOW  "\033[38;5;99m"
#define BLUE    "\033[38;5;189m"
#define MAGENTA "\033[38;5;219m"
#define CYAN    "\033[38;5;225m"
 */

#define RESET       "\033[0m"
#define BOLD        "\033[1m"
#define DARK_PINK   "\033[38;5;205m"
#define DARK_YELLOW "\033[38;5;228m"
#define LIGHT_YELLOW "\033[38;5;230m"
#define GREEN       "\033[38;5;158m"
#define LIGHT_YELLOW "\033[38;5;230m"
#define MAGENTA     "\033[38;5;219m"
#define DARK_GREEN   "\033[38;5;49m"
#define GRAY   "\033[38;5;236m"

void clear_screen()
{
    std::cout << "\033[2J\033[H";
}


void print_header(int leak_num, int total_leaks)
{
    std::cout
        << DARK_GREEN
        << "―――――――――――――+――――――――――――――――――――――――\n"
        << "‣ Leak "
        << leak_num
        << " / "
        << total_leaks
        << " | Valgrind Error eXplorer\n"
        << "―――――――――――――+――――――――――――――――――――――――"
        << std::endl
        << RESET;
}

void print_valgrind(void)
{
    std::cout
        << LIGHT_YELLOW
/*         << "----------------------------------------------------------------------------------------\n" */
        << "68 (16 direct, 52 indirect) bytes in 1 blocks are definitely lost in loss record 8 of 10\n"
        << "    at 0x4848899: malloc (in /usr/libexec/valgrind/vgpreload_memcheck-amd64-linux.so)\n"
        << "    by 0x109256: create_node_leaked (leaky.c:19)\n"
        << "    by 0x1094F2: leak_type3_broken_linked_list (leaky.c:81)\n"
        << "    by 0x1095C5: main (leaky.c:113)\n"
/*         << "----------------------------------------------------------------------------------------\n" */
        << RESET;
}

void print_title(const std::string& title)
{
    std::cout
        << "\n"
        << GREEN
        << "• "
        << title
        << RESET
        << "\n"
        << std::endl;
}

void print_diagnostic(const std::string& leak_type, const std::string& content)
{
    std::cout
        << DARK_YELLOW
        << "→ "
        << leak_type
        << "\n\n";
    
    std::cout
        << LIGHT_YELLOW
        << content
        << "\n";
}

void print_context(const std::string& file, const std::string& function)
{
    std::cout
        << LIGHT_YELLOW
        << "Fichier  : "
        << file
        << "\n"
        << "Fonction : "
        << function
        << RESET
        << "\n"
        << std::endl;
}

void print_resolution(const std::string& content)
{
    std::cout
        << LIGHT_YELLOW
        << content
        << RESET
        << "\n";
}

void print_error_code(int start_line, int error_line)
{  
    std::cout
        << "   "
        << start_line
        << " |     Node *third = head->next->next;\n";
    
    // Ligne avec l'erreur en rouge
    std::cout
        << DARK_PINK
        << "‣  "
        << error_line
        << " |     head->next = NULL;"
        << GRAY
        << " // Détruit la référence vers les nœuds suivants, rendant leur mémoire inaccessible"
        << RESET
        << "\n";
    
    std::cout
        << "   "
        << (error_line + 1)
        << " |     free(head->data);\n";
}

void print_code(void)
{
    std::cout << "\n";
    std::cout << "Node *current = head->next;\n";
    std::cout << "while (current != NULL)\n";
    std::cout << "{\n";
    std::cout << "  Node *next = current->next;\n";
    std::cout << "  free(current->data);\n";
    std::cout << "  free(current);\n";
    std::cout << "  current = next;\n";
    std::cout << "}\n";
}

void print_explications(const std::string& content)
{
    std::cout
        << LIGHT_YELLOW
        << content
        << std::endl;
}

void print_menu()
{
    std::cout
        << "\n";
    
    std::cout
        << std::endl
        << MAGENTA
        << "[ENTRÉE]"
        << RESET
        << " Marquer comme corrigé et passer au suivant\n";
    
    std::cout
        << MAGENTA
        << "[V]     "
        << RESET
        << " Vérifier avec Valgrind\n";
    
    std::cout
        << MAGENTA
        << "[Q]     "
        << RESET
        << " Quitter\n";
    
    std::cout
        << RESET;
}

int main()
{
    clear_screen();
    
    // Affichage du leak
    print_header(1, 2);

    print_title("Extrait Valgrind");

    print_valgrind();

    print_title("Analyse Vex");
    
    print_diagnostic("Plus aucun pointeur ne permet d'accéder à la mémoire allouée", "Dans leak_type3_broken_linked_list() les nœuds second, third et fourth ne sont jamais libérés car ils deviennent inaccessibles après head->next = NULL.");
    
/*     print_title("Allocation");

    print_context("leaky.c:19", "create_node_leaked");

    std::cout
        << "   19 | Node *n = malloc(sizeof(Node));"
        << std::endl; */

   print_title("Code conerné");

    print_context("leaky.c:87", "leak_type3_broken_linked_list");
    
    print_error_code(86, 87);

    print_title("Solution");
    
    print_resolution("Dans leak_type3_broken_linked_list(), libérer tous les nœuds suivants (second, third, fourth) avant head->next = NULL.");
    
    print_code();

    print_title("Explications");

    print_explications("Cela libère correctement tous les nœuds avant de casser le chaînage, empêchant la perte de la seule référence restante.");

    print_menu();
    
    // Attente d'input utilisateur
    std::cout
        << "\n"
        << DARK_GREEN
        << "vex > "
        << RESET;
    
    std::string choice;
    std::getline(std::cin, choice);
    
    // Gestion des choix
    if (choice.empty())
    {
        std::cout << GREEN << "✅ Leak #1 marqué comme corrigé\n" << RESET;
    }
    else if (choice == "v")
    {
        std::cout << GREEN << "⏳ Relance de Valgrind pour vérifier...\n" << RESET;
    }
    else if (choice == "q")
    {
        std::cout << LIGHT_YELLOW << "👋 Au revoir !\n" << RESET;
    }
    
    return 0;
}
#include <iostream>
#include <fstream>
#include <string>
#include <unistd.h>
#include <iterator>

#define RESET       "\033[0m"
#define BOLD        "\033[1m"
#define DARK_PINK   "\033[38;5;205m"
#define DARK_YELLOW "\033[38;5;228m"
#define LIGHT_YELLOW "\033[38;5;230m"
#define GREEN       "\033[38;5;158m"
#define LIGHT_YELLOW "\033[38;5;230m"
#define MAGENTA     "\033[38;5;219m"
#define DARK_GREEN   "\033[38;5;49m"

void clear_screen()
{
    std::cout << "\033[2J\033[H";
}

void printLogo(const std::string& filename)
{
    std::ifstream file(filename);
    if (!file.is_open())
    {
        std::cerr << "Impossible d'ouvrir le fichier : " << filename << std::endl;
        return;
    }

    std::string line;
    while (std::getline(file, line))
    {
        std::cout
            << DARK_GREEN
            << line
            << RESET 
            << std::endl;
    }
   std::cout << std::endl;
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
        << " Commencer la résolution\n";
    
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
    printLogo("logo.txt");

    std::cout
        /* << DARK_GREEN */
        << "Valgrind Error Explorer\n"
        << GREEN
        << "Mistral AI intership project"
        << RESET
        << std::endl
        << std::endl;

    std::string spinner [] = {"◌", "○", "◎", "◉", "◍", "●"};
    std::string spinner_2 [] = {"▙", "▛", "▜", "▟"};
    std::string spinner_3 [] = {"▴", "▸", "▾", "◂"};
    std::string spinner_4 [] = {"◐", "◓", "◑", "◓"};
    std::string spinner_5 [] = {"○", "☐", "◇"};
    std::string spinner_6 [] = {"▶", "▷"};
    std::string spinner_7 [] = {"✦", "✪", "✺", "✻", "✿", "✭", "❈"};

    size_t spinner_size = sizeof(spinner_7) / sizeof(spinner_7[0]);

    int i = 0;

    while (i < 50)
    {
        std::cout
            << "\r"
            << spinner_7[i % spinner_size]
            << " Lancement de valgrind"
            << std::flush;

        usleep(100000);
        i++;
    }

    std::cout 
        << "\r"
        << GREEN
        << "✓"
        << RESET
        << std::endl;

        int j = 0;

    while (j < 5)
    {
        std::cout
            << "\r"
            << spinner_7[j % spinner_size]
            << " Parsing du rapport"
            << std::flush;

        usleep(100000);
        j++;
    }

    std::cout 
        << "\r"
        << GREEN
        << "✓"
        << RESET
        << std::endl;

            int k = 0;

    while (k < 5)
    {
        std::cout
            << "\r"
            << spinner_7[k % spinner_size]
            << " Exctraction du code source"
            << std::flush;

        usleep(100000);
        k++;
    }

    std::cout 
        << "\r"
        << GREEN
        << "✓"
        << RESET
        << std::endl;


            int l = 0;

    while (l < 5)
    {
        std::cout
            << "\r"
            << spinner_7[l % spinner_size]
            << " Interrogation de Mistral AI"
            << std::flush;

        usleep(100000);
        l++;
    }

    std::cout 
        << "\r"
        << GREEN
        << "✓"
        << RESET
        << std::endl
        << std::endl;

    std::cout
        << GREEN
        << "• Résumé du rapport Valgrind : "
        << RESET
        << std::endl
        << std::endl;

      std::cout
        << LIGHT_YELLOW
        << "------------------------------\n"
        << DARK_YELLOW
        << "3"
        << LIGHT_YELLOW
        << " fuites de mémoires détéctées\n"
        << "------------------------------\n"
        << "    Definitely lost : 71 bytes\n"
        << "------------------------------\n"
        << "    inderectly lost : 54 bytes\n"
        << "------------------------------\n"
        << DARK_YELLOW
        << "‣ Total : 125 bytes"
        << std::endl;

    print_menu();
    
    // Attente d'input utilisateur
    std::cout
        << "\n"
        << DARK_GREEN
        << "vex > "
        << RESET;
    
    std::string choice;
    std::getline(std::cin, choice);



    return (0);
}

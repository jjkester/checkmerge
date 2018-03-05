#define NAME_LENGTH 20
#define KEEP_ORDERED 0

typedef struct {
    int number;
    char name[NAME_LENGTH];
} data;

typedef struct node_s {
    data* data;
    struct node_s* prev;
    struct node_s* next;
} node;

typedef struct {
    node* head;
    node* tail;
} dll;

/**
 * @brief Compares @c d1 and @c d2
 * @param d1 Data to be compared
 * @param d2 Data to be compared
 * @return -1 if d1 < d2, 1 if d2 > 1, 0 otherwise
 */
int data_compare(data* d1, data* d2);

/**
 * @brief Prints the data @c to FILE @c f
 * @param d The data to print
 * @param f The FILE to print to
 */
void data_print(data* d, FILE* f);

/**
 * @brief Creates a new data using the specified @c age and @c name
 * @param age The age
 * @param name The name
 * @return Pointer to a new data instance
 */
data* data_new(int age, char const* name);

/**
 * @brief Deletes the specified data and frees its memory
 * @param d The data to delete
 */
void data_delete(data* d);

/**
 * @brief Creates a new DLL, Doubly Linked List
 * @return Pointer to a new DLL instance
 */
dll* dll_new();

/**
 * @brief Inserts @c data into the DLL, at the end
 * @param dll The DLL into which data is to be inserted
 * @param data The data to be inserted
 */
void dll_insert(dll* dll, data* data);

/**
 * @brief Erases the first element in the DLL that is equal to @c data
 * @param dll The DLL into which data is to be erased
 * @param data The data to be erased
 */
void dll_erase(dll* dll, data* data);

/**
 * @brief Prints the elements in the DLL
 * @param dll The DLL to print
 * @param printFile The FILE to print to
 */
void dll_print(dll* dll, FILE* printFile);

/**
 * @brief Reverses the order of elements in the DLL
 * @param dll The DLL of which the order of its elements is to be reversed
 */
void dll_inverse(dll* dll);

/**
 * @brief Deletes the DLL and frees all its memory
 * @param dll The DLL to delete
 */
void dll_delete(dll* dll);

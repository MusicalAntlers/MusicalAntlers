// Random random = new Random();
// int randomNumber = random.Next() % 2;
// string coinFlip = randomNumber == 0 ? "heads" : "tails";
// Console.WriteLine(coinFlip);

Random random = new Random();
int flip = random.Next(0, 2);
Console.WriteLine((flip == 0) ? "heads" : "tails");

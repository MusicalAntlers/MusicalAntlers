string? readResult;
string roleName = "";
bool validEntry = false;


do
{
  Console.WriteLine("Enter your role name (Administrator, Manager, or User)");
  readResult = Console.ReadLine();
  if (readResult != null)
  {
    roleName = readResult.Trim();
  }
  if (roleName.ToLower() == "administrator" || roleName.ToLower() == "manager" || roleName.ToLower() == "user")
  {
    validEntry = true;
  }
  else
  {
    Console.WriteLine($"The role name you entered \"{roleName}\" is not valid. Enter your role name (Administrator, Manager, or User).");
  }
} while (validEntry == false);

Console.WriteLine($"Your input value ({roleName}) has been accepted.");
readResult = Console.ReadLine();

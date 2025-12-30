using System.Data.Common;

string[] fraudulentOrderIDs = ["B123", "C234", "A345", "C15", "B177", "G3003", "C235", "B179"];
foreach (string id in fraudulentOrderIDs)
{
    if (id.StartsWith("B"))
    {
        Console.WriteLine(id);
    }
}

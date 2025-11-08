<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\EscposCommand;

class CommandOneArg extends EscposCommand
{
    private ?int $arg = null;

    public function addChar($char)
    {
        if ($this -> arg === null) {
            $this -> arg = ord($char);
            return true;
        } else {
            return false;
        }
    }
    
    protected function getArg(): ?int
    {
        return $this -> arg;
    }
}

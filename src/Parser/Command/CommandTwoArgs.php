<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\EscposCommand;

class CommandTwoArgs extends EscposCommand
{
    private ?int $arg1 = null;
    private ?int $arg2 = null;

    public function addChar($char)
    {
        if ($this -> arg1 === null) {
            $this -> arg1 = ord($char);
            return true;
        } elseif ($this -> arg2 === null) {
            $this -> arg2 = ord($char);
            return true;
        }
        return false;
    }

    protected function getArg1(): ?int
    {
        return $this -> arg1;
    }

    protected function getArg2(): ?int
    {
        return $this -> arg2;
    }
}
